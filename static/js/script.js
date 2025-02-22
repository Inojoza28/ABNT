document.addEventListener('DOMContentLoaded', () => {
  const inputs = document.querySelectorAll('[data-check]');
  const generateBtn = document.getElementById('generateBtn');

  function validateForm() {
      let isValid = true;
      inputs.forEach(input => {
          if (!input.value.trim()) isValid = false;
      });
      generateBtn.disabled = !isValid;
  }

  inputs.forEach(input => {
      input.addEventListener('input', validateForm);
      input.addEventListener('change', validateForm);
  });

  validateForm();
});