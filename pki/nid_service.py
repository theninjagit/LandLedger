"""
ID Verification Service
-----------------------
NID : lookup by NID number  → check name + DOB + mobile
PAN : lookup by PHONE number → check name only  (phone IS the unique ID for PAN)
"""
import hashlib, re
from datetime import datetime

# ── Mock citizen database ──────────────────────────────────────────────────────
MOCK_CITIZENS = {
    # KEY = 10-digit NID number
    "nid": {
        "1234567890": {"full_name": "Ram Bahadur Thapa",      "dob": "1985-04-12", "mobile": "9841000001", "address": "Baneshwor-10, Kathmandu"},
        "0987654321": {"full_name": "Sita Kumari Sharma",     "dob": "1990-08-25", "mobile": "9841000002", "address": "Lalitpur-3, Patan"},
        "1122334455": {"full_name": "Hari Prasad Adhikari",   "dob": "1975-01-30", "mobile": "9841000003", "address": "Bhaktapur-4"},
        "5544332211": {"full_name": "Gita Devi Poudel",       "dob": "1988-11-15", "mobile": "9841000004", "address": "Chitwan-5, Bharatpur"},
        "9988776655": {"full_name": "Krishna Kumar Bhandari", "dob": "1970-06-20", "mobile": "9841000005", "address": "Pokhara-6"},
        "1111111111": {"full_name": "Rajesh Hamal",           "dob": "1982-03-05", "mobile": "9841000006", "address": "Kalanki-15, Kathmandu"},
        "2222222222": {"full_name": "Anita Karki",            "dob": "1993-07-18", "mobile": "9841000007", "address": "Boudha-6, Kathmandu"},
        "3333333333": {"full_name": "Dipak Raj Joshi",        "dob": "1968-12-22", "mobile": "9841000008", "address": "Bhairahawa-3, Rupandehi"},
        "4444444444": {"full_name": "Sunita Thapa Magar",     "dob": "1995-02-14", "mobile": "9841000009", "address": "Pokhara-11"},
        "5555555555": {"full_name": "Bikash Gurung",          "dob": "1980-09-09", "mobile": "9841000010", "address": "Biratnagar-4, Morang"},
        "6666666666": {"full_name": "Kamala Shrestha",        "dob": "1992-05-30", "mobile": "9841000011", "address": "Dharan-8, Sunsari"},
        "7777777777": {"full_name": "Nabin Pradhan",          "dob": "1987-10-03", "mobile": "9841000012", "address": "Itahari-2, Sunsari"},
        "8888888888": {"full_name": "Rekha Basnet",           "dob": "1991-12-25", "mobile": "9841000013", "address": "Hetauda-4, Makwanpur"},
        "9999999990": {"full_name": "Suresh Lama",            "dob": "1978-07-07", "mobile": "9841000014", "address": "Butwal-10, Rupandehi"},
        "1234512345": {"full_name": "Puja Maharjan",          "dob": "1996-03-21", "mobile": "9841000015", "address": "Kirtipur-3, Kathmandu"},
    },
    # KEY = phone number (phone IS the PAN unique identifier)
    "pan": {
        "9851000001": {"full_name": "Mohan Kumar Shrestha",  "address": "New Baneshwor, Kathmandu"},
        "9851000002": {"full_name": "Priya Rana",            "address": "Lazimpat, Kathmandu"},
        "9851000003": {"full_name": "Anil Bajracharya",      "address": "Thamel, Kathmandu"},
        "9851000004": {"full_name": "Mina Tamang",           "address": "Jorpati, Kathmandu"},
        "9851000005": {"full_name": "Santosh Khadka",        "address": "Chabahil, Kathmandu"},
        "9851000006": {"full_name": "Rajan Subedi",          "address": "Naxal, Kathmandu"},
        "9851000007": {"full_name": "Sarita Pandey",         "address": "Pulchowk, Lalitpur"},
        "9851000008": {"full_name": "Ramesh Oli",            "address": "Banepa, Kavrepalanchok"},
        "9851000009": {"full_name": "Kabita Rai",            "address": "Urlabari, Morang"},
        "9851000010": {"full_name": "Suman Limbu",           "address": "Taplejung Bazaar"},
        "9851000011": {"full_name": "Deepa Shrestha",        "address": "Baneshwor, Kathmandu"},
        "9851000012": {"full_name": "Naresh Tamang",         "address": "Balaju, Kathmandu"},
        "9851000013": {"full_name": "Sunita Gurung",         "address": "Pokhara-8"},
        "9851000014": {"full_name": "Bijay Karmacharya",     "address": "Lalitpur-5"},
        "9851000015": {"full_name": "Anupama Basnet",        "address": "Durbarmarg, Kathmandu"},
    }
}


def _normalize(s):
    return ' '.join(str(s).lower().strip().split())

def _names_match(input_name, db_name):
    a = _normalize(input_name)
    b = _normalize(db_name)
    if a == b: return True
    aw, bw = set(a.split()), set(b.split())
    if aw <= bw: return True           # all input words in db name
    if bw <= aw: return True           # all db words in input
    if len(aw & bw) >= 2: return True  # at least 2 words match
    return False

def _clean_phone(p):
    return re.sub(r'\D', '', str(p))


def verify_id(id_type, id_number, full_name, mobile, dob=None, existing_id=None):
    """
    NID: id_number=NID(10 digits), checks name + DOB + mobile
    PAN: id_number is ignored — mobile IS the lookup key, checks name only
    """

    if id_type == 'nid':
        # ── NID FLOW ──────────────────────────────────────────────────
        clean_nid = re.sub(r'\D', '', str(id_number))
        citizen = MOCK_CITIZENS['nid'].get(clean_nid)

        if not citizen:
            return {"verified": False, "status": "not_found",
                    "message": f"NID number {clean_nid} not found in the National ID database. Please check the number.",
                    "token": None}

        if not _names_match(full_name, citizen['full_name']):
            return {"verified": False, "status": "name_mismatch",
                    "message": "Name does not match NID records. Enter your name exactly as on your NID card.",
                    "token": None}

        # DOB check
        if not dob:
            return {"verified": False, "status": "missing_dob",
                    "message": "Date of birth is required for NID verification.",
                    "token": None}
        try:
            datetime.strptime(dob, '%Y-%m-%d')
        except ValueError:
            return {"verified": False, "status": "invalid_dob",
                    "message": "Date of birth must be YYYY-MM-DD format.",
                    "token": None}
        if dob != citizen['dob']:
            return {"verified": False, "status": "dob_mismatch",
                    "message": "Date of birth does not match NID records.",
                    "token": None}

        # Mobile check
        if _clean_phone(mobile) != _clean_phone(citizen['mobile']):
            return {"verified": False, "status": "mobile_mismatch",
                    "message": "Mobile number does not match NID records.",
                    "token": None}

        if existing_id is not None:
            return {"verified": False, "status": "already_registered",
                    "message": "This NID number is already registered. Please login instead.",
                    "token": None}

        token = hashlib.sha256(f"nid{clean_nid}{_normalize(full_name)}".encode()).hexdigest()
        return {"verified": True, "status": "verified",
                "message": f"NID verified! Welcome, {citizen['full_name']}.",
                "token": token}

    elif id_type == 'pan':
        # ── PAN FLOW — phone number IS the unique ID ───────────────────
        clean_phone = _clean_phone(mobile)
        citizen = MOCK_CITIZENS['pan'].get(clean_phone)

        if not citizen:
            return {"verified": False, "status": "not_found",
                    "message": f"Phone number {clean_phone} not found in PAN database. "
                               f"Use one of the phone numbers from the PAN table below.",
                    "token": None}

        if not _names_match(full_name, citizen['full_name']):
            return {"verified": False, "status": "name_mismatch",
                    "message": f"Name does not match PAN records for this phone number. "
                               f"Expected name: {citizen['full_name']}",
                    "token": None}

        if existing_id is not None:
            return {"verified": False, "status": "already_registered",
                    "message": "This phone number is already registered. Please login instead.",
                    "token": None}

        token = hashlib.sha256(f"pan{clean_phone}{_normalize(full_name)}".encode()).hexdigest()
        return {"verified": True, "status": "verified",
                "message": f"PAN verified! Welcome, {citizen['full_name']}.",
                "token": token}

    else:
        return {"verified": False, "status": "invalid_type",
                "message": "Invalid ID type selected.", "token": None}


def get_mock_citizens():
    return MOCK_CITIZENS
