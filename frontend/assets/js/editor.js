// === Rich Text Editor ===
function initEditor() {
  const editor = document.getElementById('editor');
  if (!editor) return;

  editor.addEventListener('input', () => {
    document.getElementById('content-value').value = editor.innerHTML;
  });

  const buttons = {
    bold:    { cmd: 'bold',    html: '<b>B</b>' },
    italic:  { cmd: 'italic',  html: '<i>I</i>' },
    h1:      { cmd: 'formatBlock', val: 'H1', html: 'H1' },
    h2:      { cmd: 'formatBlock', val: 'H2', html: 'H2' },
    h3:      { cmd: 'formatBlock', val: 'H3', html: 'H3' },
    p:       { cmd: 'formatBlock', val: 'P',  html: '¶' },
    ul:      { cmd: 'insertUnorderedList', html: '• List' },
    ol:      { cmd: 'insertOrderedList', html: '1. List' },
    link:    { cmd: 'insertLink', html: '🔗' },
    image:   { cmd: 'insertImage', html: '🖼️' },
    video:   { cmd: 'insertVideo', html: '🎬' },
    quote:   { cmd: 'formatBlock', val: 'BLOCKQUOTE', html: '❝' },
    code:    { cmd: 'formatBlock', val: 'PRE', html: '<>' },
  };

  Object.entries(buttons).forEach(([key, cfg]) => {
    const btn = document.querySelector(`.editor-toolbar [data-cmd="${key}"]`);
    if (btn) {
      btn.addEventListener('click', async () => {
        if (key === 'link') {
          const url = prompt('Enter URL:');
          if (url) document.execCommand('insertHyperlink', false, url);
        } else if (key === 'image') {
          const url = prompt('Enter image URL:');
          if (url) document.execCommand('insertImage', false, url);
        } else if (key === 'video') {
          const url = prompt('Enter video URL (YouTube/Bilibili):');
          if (url) {
            const iframe = `<br><iframe src="${url}" width="640" height="360" frameborder="0" allowfullscreen></iframe><br>`;
            document.execCommand('insertHTML', false, iframe);
          }
        } else {
          document.execCommand(cfg.cmd, false, cfg.val || null);
        }
        editor.focus();
      });
    }
  });
}

async function uploadCover(file) {
  const formData = new FormData();
  formData.append('file', file);
  const token = getToken();
  const res = await fetch(`${API_BASE}/media/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${token}` },
    body: formData,
  });
  const data = await res.json();
  return data.data?.url || null;
}