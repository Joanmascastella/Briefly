document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('news-search-form');

    form.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent the form's default behavior

        const formData = {
            title: document.getElementById('title').value,
            keywords: document.getElementById('keywords').value,
            publishers: document.getElementById('publishers').value,
            date_range: document.getElementById('date-range').value,
        };

        await searchNews(formData);
    });
});

async function searchNews(formData) {
    const searchURL = `/${window.location.pathname.split('/')[1]}/search/`;

    try {
        const response = await fetch(searchURL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                "X-CSRFToken": document.querySelector('[name=csrfmiddlewaretoken]').value,
            },
            body: JSON.stringify(formData),
        });

        if (!response.ok) {
            const errorData = await response.json();
            showMessage(errorData.error || 'An error occurred while fetching news.', 'danger');
            return;
        }

        const data = await response.json();
        showMessage('Search completed successfully!', 'success');

        const resultsContainer = document.getElementById('search-results');
        resultsContainer.innerHTML = data.articles
            .map(article => `
                <div class="card mb-3">
                    <img src="${article.image}" class="card-img-top" alt="${article.title}">
                    <div class="card-body">
                        <h5 class="card-title">${article.title}</h5>
                        <p class="card-text">${article.publisher} - ${article.date}</p>
                        <a href="${article.link}" target="_blank" class="btn btn-primary">Read More</a>
                    </div>
                </div>
            `)
            .join('');
    } catch (error) {
        showMessage('A network error occurred. Please try again.', 'danger');
    }
}

function showMessage(message, type) {
    const messageBox = document.getElementById('messageBox');
    messageBox.textContent = message;
    messageBox.className = `alert alert-${type}`;
    messageBox.classList.remove('d-none');

    setTimeout(() => {
        messageBox.classList.add('d-none');
    }, 3000);
}