// 에러 메시지 초기화
function clearError(id) {
  const el = document.getElementById(id);
  if (el) el.innerText = '';
}

// 입력 시 에러 메시지 제거
document.querySelectorAll('input').forEach(input => {
  input.addEventListener('input', () => {
    const errorId = input.name.replace(/_/g, '-') + '-error';
    clearError(errorId);
  });
});

// 로그인 유효성 검사
function validateLogin() {
  const form = document.querySelector('form.sign-in');
  const loginId = form.querySelector('input[name="login_id"]').value.trim();
  const password = form.querySelector('input[name="password"]').value.trim();
  let valid = true;

  if (!loginId) {
    document.getElementById('login-id-error').innerText = '아이디를 입력해주세요.';
    valid = false;
  } else {
    clearError('login-id-error');
  }

  if (!password) {
    document.getElementById('login-password-error').innerText = '비밀번호를 입력해주세요.';
    valid = false;
  } else {
    clearError('login-password-error');
  }

  return valid;
}

// AJAX 로그인 처리
document.addEventListener('DOMContentLoaded', () => {
  const loginForm = document.querySelector('form.sign-in');
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (!validateLogin()) return;

      clearError('login-id-error');
      clearError('login-password-error');

      const formData = new FormData(loginForm);
      const res = await fetch('/login', {
        method: 'POST',
        body: formData
      });

      const result = await res.json();

      if (result.success) {
        window.location.href = result.redirect;
      } else {
        if (result.message.includes('아이디')) {
          document.getElementById('login-id-error').innerText = result.message;
        } else if (result.message.includes('비밀번호')) {
          document.getElementById('login-password-error').innerText = result.message;
        }
      }
    });
  }

  // AJAX 회원가입 처리
  const signupForm = document.querySelector('form.sign-up');
  if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
      e.preventDefault();

      if (!validateSignup()) return;

      // 모든 에러 메시지 초기화
      ['id', 'password', 'confirm-password', 'name', 'phone', 'gender', 'birthday'].forEach(field => {
        clearError(field + '-error');
      });

      const formData = new FormData(signupForm);
      const res = await fetch('/signup', {
        method: 'POST',
        body: formData
      });

      const result = await res.json();

      if (result.success) {
        alert(result.message);
        document.querySelector('.pointer').click(); // 로그인 탭으로 전환
      } else {
        const field = result.field || 'id';
        const errorBox = document.getElementById(field + '-error');
        if (errorBox) errorBox.innerText = result.message;
      }
    });
  }
});

// 회원가입 유효성 검사
function validateSignup() {
  const form = document.querySelector('form.sign-up');
  const id = form.querySelector('input[name="login_id"]').value.trim();
  const pw = form.querySelector('input[name="password"]').value.trim();
  const pw2 = form.querySelector('input[name="confirm_password"]').value.trim();
  const name = form.querySelector('input[name="uname"]').value.trim();
  const phone = form.querySelector('input[name="phone"]').value.trim();
  const gender = form.querySelector('input[name="gender"]:checked');
  const birth = form.querySelector('input[name="birthday"]').value.trim();

  const idRegex = /^[a-z0-9]{6,20}$/;
  const pwRegex = /^(?=.*[A-Za-z])(?=.*\d)(?=.*[!@#$%^&*])[A-Za-z\d!@#$%^&*]{8,20}$/;

  let valid = true;

  if (!id || !idRegex.test(id)) {
    document.getElementById('id-error').innerText = '소문자와 숫자로 구성된 6~20자 아이디여야 합니다.';
    valid = false;
  } else {
    clearError('id-error');
  }

  if (!pw || !pwRegex.test(pw)) {
    document.getElementById('password-error').innerText = '문자, 숫자, 특수문자를 포함한 8~20자 비밀번호여야 합니다.';
    valid = false;
  } else {
    clearError('password-error');
  }

  if (pw !== pw2) {
    document.getElementById('confirm-password-error').innerText = '비밀번호가 일치하지 않습니다.';
    valid = false;
  } else {
    clearError('confirm-password-error');
  }

  if (!name) {
    document.getElementById('name-error').innerText = '이름을 입력해주세요.';
    valid = false;
  } else {
    clearError('name-error');
  }

  if (!phone) {
    document.getElementById('phone-error').innerText = '연락처를 입력해주세요.';
    valid = false;
  } else {
    clearError('phone-error');
  }

  if (!gender) {
    document.getElementById('gender-error').innerText = '성별을 선택해주세요.';
    valid = false;
  } else {
    clearError('gender-error');
  }

  if (!birth) {
    document.getElementById('birthday-error').innerText = '생년월일을 입력해주세요.';
    valid = false;
  } else {
    clearError('birthday-error');
  }

  return valid;
}
