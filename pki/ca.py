import datetime
import os
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.exceptions import InvalidSignature

CERTS_DIR = os.path.join(os.path.dirname(__file__), '..', 'certs')
os.makedirs(CERTS_DIR, exist_ok=True)


def generate_rsa_keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)

def private_key_to_pem(key):
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    ).decode()

def public_key_to_pem(key):
    pub = key.public_key() if hasattr(key, 'private_bytes') else key
    return pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

def cert_to_pem(cert):
    return cert.public_bytes(serialization.Encoding.PEM).decode()

def load_private_key(pem):
    return serialization.load_pem_private_key(pem.encode(), password=None)

def load_certificate(pem):
    return x509.load_pem_x509_certificate(pem.encode())

def load_public_key(pem):
    return serialization.load_pem_public_key(pem.encode())


class LandLedgerCA:
    def __init__(self):
        self.ca_key = None
        self.ca_cert = None
        self._init_ca()

    def _init_ca(self):
        key_path = os.path.join(CERTS_DIR, 'ca.key.pem')
        cert_path = os.path.join(CERTS_DIR, 'ca.cert.pem')
        if os.path.exists(key_path) and os.path.exists(cert_path):
            with open(key_path) as f:
                self.ca_key = load_private_key(f.read())
            with open(cert_path) as f:
                self.ca_cert = load_certificate(f.read())
        else:
            self._create_ca()

    def _create_ca(self):
        now = datetime.datetime.utcnow()
        self.ca_key = generate_rsa_keypair()
        name = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "NP"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Bagmati"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Kathmandu"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "LandLedger Authority"),
            x509.NameAttribute(NameOID.COMMON_NAME, "LandLedger CA"),
        ])
        self.ca_cert = (
            x509.CertificateBuilder()
            .subject_name(name).issuer_name(name)
            .public_key(self.ca_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=3650))
            .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
            .add_extension(x509.KeyUsage(
                digital_signature=True, key_cert_sign=True, crl_sign=True,
                content_commitment=False, key_encipherment=False,
                data_encipherment=False, key_agreement=False,
                encipher_only=False, decipher_only=False
            ), critical=True)
            .sign(self.ca_key, hashes.SHA256())
        )
        with open(os.path.join(CERTS_DIR, 'ca.key.pem'), 'w') as f:
            f.write(private_key_to_pem(self.ca_key))
        with open(os.path.join(CERTS_DIR, 'ca.cert.pem'), 'w') as f:
            f.write(cert_to_pem(self.ca_cert))

    def issue_certificate(self, common_name, email, role):
        key = generate_rsa_keypair()
        now = datetime.datetime.utcnow()
        subject = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "NP"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, f"LandLedger - {role}"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.EMAIL_ADDRESS, email),
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject).issuer_name(self.ca_cert.subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=365))
            .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
            .add_extension(x509.KeyUsage(
                digital_signature=True, content_commitment=True,
                key_encipherment=False, data_encipherment=False,
                key_agreement=False, key_cert_sign=False,
                crl_sign=False, encipher_only=False, decipher_only=False
            ), critical=True)
            .sign(self.ca_key, hashes.SHA256())
        )
        return {
            'private_key_pem': private_key_to_pem(key),
            'public_key_pem': public_key_to_pem(key),
            'cert_pem': cert_to_pem(cert),
            'serial_number': str(cert.serial_number),
        }

    def verify_certificate(self, cert_pem):
        try:
            cert = load_certificate(cert_pem)
            self.ca_cert.public_key().verify(
                cert.signature, cert.tbs_certificate_bytes,
                PKCS1v15(), hashes.SHA256()
            )
            now = datetime.datetime.utcnow()
            if now < cert.not_valid_before_utc.replace(tzinfo=None):
                return False, "Certificate not yet valid"
            if now > cert.not_valid_after_utc.replace(tzinfo=None):
                return False, "Certificate expired"
            return True, "Certificate valid"
        except InvalidSignature:
            return False, "Invalid certificate signature"
        except Exception as e:
            return False, str(e)

    def sign_data(self, data: bytes, private_key_pem: str) -> bytes:
        key = load_private_key(private_key_pem)
        return key.sign(data, PKCS1v15(), hashes.SHA256())

    def verify_signature(self, data: bytes, signature: bytes, public_key_pem: str) -> bool:
        try:
            pub_key = load_public_key(public_key_pem)
            pub_key.verify(signature, data, PKCS1v15(), hashes.SHA256())
            return True
        except Exception:
            return False

    def get_ca_info(self):
        return {
            'common_name': 'LandLedger CA',
            'organization': 'LandLedger Authority',
            'country': 'NP',
            'valid_from': self.ca_cert.not_valid_before_utc.strftime('%Y-%m-%d'),
            'valid_until': self.ca_cert.not_valid_after_utc.strftime('%Y-%m-%d'),
            'serial_number': str(self.ca_cert.serial_number),
            'cert_pem': cert_to_pem(self.ca_cert),
        }

ca = LandLedgerCA()
