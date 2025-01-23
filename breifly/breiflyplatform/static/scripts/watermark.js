document.addEventListener('DOMContentLoaded', function () {
  const watermark = document.getElementById('watermark');
  const staticUrl = watermark.getAttribute('data-static-url'); // Get the static URL

  // Create container for watermark content
  const watermarkContent = document.createElement('div');
  watermarkContent.classList.add('d-flex', 'align-items-center', 'px-3', 'py-2');

  // Create image element
  const logo = document.createElement('img');
  logo.src = staticUrl + 'smartis-ai-logo.png'; // Append the logo filename
  logo.alt = 'Smartis AI Logo';
  logo.classList.add('me-2');
  logo.style.height = '24px';

  // Create text element
  const text = document.createElement('span');
  text.textContent = 'Powered by Smartis AI';
  text.classList.add('fw-bold', 'fs-6');

  // Append elements to watermark container
  watermarkContent.appendChild(logo);
  watermarkContent.appendChild(text);

  // Apply styles for pill shape, white background, and black border
  watermarkContent.style.backgroundColor = 'white';
  watermarkContent.style.border = '1px solid black';
  watermarkContent.style.borderRadius = '50px';

  // Add animation
  watermarkContent.style.animation = 'float 3s ease-in-out infinite';

  // Append to watermark container
  watermark.appendChild(watermarkContent);
});