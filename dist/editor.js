const selection = document.querySelector('input[name="slides"]');
if (selection) {
  const container = document.getElementById('slide-descriptions');
  let urls = [];
  selection.addEventListener('change', () => {
    urls.forEach(url => URL.revokeObjectURL(url));
    urls = [];
    container.replaceChildren();
    [...selection.files].forEach(file => {
      const row = document.createElement('div');
      row.className = 'photo-description';
      const image = document.createElement('img');
      const url = URL.createObjectURL(file);
      urls.push(url);
      image.src = url;
      image.alt = '';
      const label = document.createElement('label');
      label.append(document.createTextNode(file.name + ' — description (optional)'));
      const input = document.createElement('input');
      input.name = 'slide_alt';
      input.maxLength = 300;
      label.append(input);
      row.append(image, label);
      container.append(row);
    });
  });
}
