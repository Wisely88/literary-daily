(() => {
  const article = document.querySelector('[data-article-id]');
  const id = article?.dataset.articleId;
  const favorite = document.querySelector('[data-favorite]');
  const favoriteKey = id ? `literary-daily:favorite:${id}` : '';
  const feedbackKey = id ? `literary-daily:feedback:${id}` : '';
  const updateFavorite = () => { if (favorite) favorite.textContent = localStorage.getItem(favoriteKey) === '1' ? '♥ 已收藏' : '♡ 收藏'; };
  favorite?.addEventListener('click', () => { const next = localStorage.getItem(favoriteKey) === '1' ? '0' : '1'; localStorage.setItem(favoriteKey, next); updateFavorite(); });
  document.querySelectorAll('[data-feedback]').forEach((button) => button.addEventListener('click', () => { if (!feedbackKey) return; localStorage.setItem(feedbackKey, button.dataset.feedback || ''); document.querySelectorAll('[data-feedback]').forEach((item) => item.setAttribute('aria-pressed', String(item === button))); }));
  updateFavorite();
})();
