// LandLedger main.js
document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alerts after 5 seconds
  document.querySelectorAll('.ll-alert').forEach(alert => {
    setTimeout(() => {
      alert.style.opacity = '0';
      alert.style.transform = 'translateY(-6px)';
      alert.style.transition = 'all .3s ease';
      setTimeout(() => alert.remove(), 300);
    }, 5000);
  });

  // Mark active sidebar links
  const path = window.location.pathname;
  document.querySelectorAll('.ll-sidebar-link').forEach(link => {
    if (link.getAttribute('href') === path) link.classList.add('active');
  });

  // Mark active nav links
  document.querySelectorAll('.ll-nav-link').forEach(link => {
    if (link.getAttribute('href') === path) link.classList.add('active');
  });
});
