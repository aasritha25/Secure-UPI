/**
 * Authentication Controller for Login and Registration
 */

document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.getElementById('loginForm');
  const registerForm = document.getElementById('registerForm');

  // One-click demo credential fillers
  const fillDemoCustomerBtn = document.getElementById('fillDemoCustomer');
  const fillDemoAdminBtn = document.getElementById('fillDemoAdmin');

  if (fillDemoCustomerBtn) {
    fillDemoCustomerBtn.addEventListener('click', () => {
      const emailInput = document.getElementById('loginEmail');
      const passwordInput = document.getElementById('loginPassword');
      if (emailInput && passwordInput) {
        emailInput.value = 'demo@secureupi.com';
        passwordInput.value = 'demo123';
        UI.showToast('Demo Customer credentials loaded!', 'info');
      }
    });
  }

  if (fillDemoAdminBtn) {
    fillDemoAdminBtn.addEventListener('click', () => {
      const emailInput = document.getElementById('loginEmail');
      const passwordInput = document.getElementById('loginPassword');
      if (emailInput && passwordInput) {
        emailInput.value = 'admin@secureupi.com';
        passwordInput.value = 'admin123';
        UI.showToast('Bank Admin credentials loaded!', 'info');
      }
    });
  }

  // Handle Login Submission
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('loginEmail').value.trim();
      const password = document.getElementById('loginPassword').value;
      const submitBtn = loginForm.querySelector('button[type="submit"]');

      if (!email || !password) {
        UI.showToast('Please enter both email and password.', 'warning');
        return;
      }

      try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Authenticating...';

        const res = await API.login({ email, password });
        AuthStore.setToken(res.access_token);
        AuthStore.setUser(res.user);

        UI.showToast(`Welcome back, ${res.user.name}!`, 'success');

        setTimeout(() => {
          if (res.user.role === 'admin') {
            window.location.href = '/admin';
          } else {
            window.location.href = '/dashboard';
          }
        }, 600);
      } catch (err) {
        UI.showToast(err.message || 'Authentication failed. Please check credentials.', 'danger');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-sign-in-alt me-2"></i>Sign In';
      }
    });
  }

  // Handle Registration Submission
  if (registerForm) {
    registerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const name = document.getElementById('regName').value.trim();
      const email = document.getElementById('regEmail').value.trim();
      const phone = document.getElementById('regPhone').value.trim();
      const password = document.getElementById('regPassword').value;
      const confirmPassword = document.getElementById('regConfirmPassword').value;
      const initialBalance = parseFloat(document.getElementById('regBalance').value) || 100000;
      const submitBtn = registerForm.querySelector('button[type="submit"]');

      if (!name || !email || !phone || !password) {
        UI.showToast('Please fill in all required registration fields.', 'warning');
        return;
      }

      if (password !== confirmPassword) {
        UI.showToast('Passwords do not match.', 'danger');
        return;
      }

      try {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Creating Account...';

        const res = await API.register({
          name,
          email,
          phone,
          password,
          initial_balance: initialBalance
        });

        AuthStore.setToken(res.access_token);
        AuthStore.setUser(res.user);

        UI.showToast('Account registered successfully!', 'success');
        setTimeout(() => {
          window.location.href = '/dashboard';
        }, 700);
      } catch (err) {
        UI.showToast(err.message || 'Registration failed.', 'danger');
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-user-plus me-2"></i>Create Account';
      }
    });
  }
});

// Logout handler
function logoutUser() {
  AuthStore.clear();
  UI.showToast('You have been logged out successfully.', 'info');
  setTimeout(() => {
    window.location.href = '/login';
  }, 400);
}
