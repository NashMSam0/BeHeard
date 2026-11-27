document.querySelectorAll('input[type="password"]').forEach((input, index) => {
  if (!input.id) input.id = 'password-field-' + index;
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'password-eye';
  button.textContent = '◉ Show';
  button.setAttribute('aria-controls', input.id);
  button.setAttribute('aria-pressed', 'false');
  button.addEventListener('click', () => {
    const reveal = input.type === 'password';
    input.type = reveal ? 'text' : 'password';
    button.textContent = reveal ? '◉ Hide' : '◉ Show';
    button.setAttribute('aria-pressed', String(reveal));
  });
  input.after(button);
});
document.querySelectorAll('form[action$="/delete"]').forEach(form => {
  form.addEventListener('submit', event => {
    if (!confirm('Move this submission to Deleted submissions? You can restore it there.')) event.preventDefault();
  });
});
