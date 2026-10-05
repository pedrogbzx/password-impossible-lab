'use strict';
document.querySelector('[data-toggle-password]')?.addEventListener('click', (event) => {
  const field = document.getElementById('password');
  field.type = field.type === 'password' ? 'text' : 'password';
  event.target.textContent = field.type === 'password' ? 'Mostrar' : 'Ocultar';
});
document.querySelector('[data-generate]')?.addEventListener('click', () => {
  // Uniform sampling of printable ASCII (33..126); reject modulo bias.
  const alphabet = Array.from({length: 94}, (_, i) => String.fromCharCode(i + 33));
  let result = '';
  while (result.length < 20) {
    for (const byte of crypto.getRandomValues(new Uint8Array(32))) {
      if (byte < 188 && result.length < 20) result += alphabet[byte % 94];
    }
  }
  const field = document.getElementById('password');
  field.value = result;
  field.type = 'text';
  document.querySelector('[data-toggle-password]').textContent = 'Ocultar';
});
