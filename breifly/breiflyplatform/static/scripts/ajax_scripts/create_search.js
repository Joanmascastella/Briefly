document.addEventListener('DOMContentLoaded', () => {
        const form = document.getElementById('news-search-form');
        const resultsContainer = document.getElementById('search-results');
        const prevPageButton = document.getElementById('prev-page');
        const nextPageButton = document.getElementById('next-page');

        let articles = [];
        let currentPage = 1;
        const articlesPerPage = 5;

        form.addEventListener('submit', async (event) => {
            event.preventDefault();

            const formData = {
                title: document.getElementById('title').value,
                keywords: document.getElementById('keywords').value,
            };

            await searchNews(formData);
        });

        async function searchNews(formData) {
            const searchURL = `/${window.location.pathname.split('/')[1]}/search/results/`;

            try {
                const response = await fetch(searchURL, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    },
                    body: JSON.stringify(formData),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    showMessage(errorData.error || 'An error occurred while fetching news.', 'danger');
                    return;
                }

                const data = await response.json();
                articles = data.articles || [];
                currentPage = 1;
                renderArticles();
                showMessage('Search completed successfully!', 'success');
            } catch (error) {
                showMessage('A network error occurred. Please try again.', 'danger');
            }
        }

        function renderArticles() {
            const startIndex = (currentPage - 1) * articlesPerPage;
            const endIndex = startIndex + articlesPerPage;
            const articlesToShow = articles.slice(startIndex, endIndex);

            resultsContainer.innerHTML = articlesToShow
                .map(article => `
                    <div class="d-flex align-items-start mb-3">
                        <div>
                            <h5>${article.title}</h5>
                            <p>${article.publisher} - ${article.date}</p>
                            <a href="${article.link}" target="_blank" class="btn btn-primary btn-sm">Read More</a>
                        </div>
                    </div>
                `)
                .join('');

            prevPageButton.disabled = currentPage === 1;
            nextPageButton.disabled = endIndex >= articles.length;
        }

        prevPageButton.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderArticles();
            }
        });

        nextPageButton.addEventListener('click', () => {
            if (currentPage * articlesPerPage < articles.length) {
                currentPage++;
                renderArticles();
            }
        });

        function showMessage(message, type) {
            const messageBox = document.getElementById('messageBox');
            messageBox.textContent = message;
            messageBox.className = `alert alert-${type}`;
            messageBox.classList.remove('d-none');

            setTimeout(() => {
                messageBox.classList.add('d-none');
            }, 3000);
        }
    });