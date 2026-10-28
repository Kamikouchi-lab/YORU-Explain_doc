(function (document) {
  // The sidebar closes on a click outside it (Lanyon, as on the YORU site).
  var toggle = document.querySelector('.sidebar-toggle');
  var sidebar = document.querySelector('#sidebar');
  var checkbox = document.querySelector('#sidebar-checkbox');

  document.addEventListener('click', function (e) {
    var target = e.target;

    if (!checkbox.checked ||
       sidebar.contains(target) ||
       (target === checkbox || target === toggle)) return;

    checkbox.checked = false;
  }, false);

  // Dark (the application's window) or light; remembered in this browser.
  var root = document.documentElement;
  var themeButton = document.querySelector('.theme-toggle');
  if (themeButton) {
    themeButton.addEventListener('click', function () {
      var next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
      root.setAttribute('data-theme', next);
      try { window.localStorage.setItem('yoru-explain-theme', next); } catch (e) {}
    });
  }

  var content = document.querySelector('.content');
  if (!content) return;

  // Wide tables scroll inside their own box instead of widening the page.
  Array.prototype.forEach.call(content.querySelectorAll('table'), function (table) {
    if (table.parentNode.classList.contains('table-wrap')) return;
    var wrap = document.createElement('div');
    wrap.className = 'table-wrap';
    table.parentNode.insertBefore(wrap, table);
    wrap.appendChild(table);
  });

  // Figures open at full size (the screenshots are small on a phone).
  Array.prototype.forEach.call(content.querySelectorAll('figure img'), function (img) {
    if (img.closest('a')) return;
    var link = document.createElement('a');
    link.href = img.getAttribute('src');
    link.title = 'Open the full-size image';
    img.parentNode.insertBefore(link, img);
    link.appendChild(img);
  });

  // "On this page" for pages with three or more sections.
  var page = content.querySelector('.page');
  if (page) {
    var headings = page.querySelectorAll('h2[id]');
    if (headings.length >= 3) {
      var nav = document.createElement('nav');
      nav.className = 'toc';
      nav.setAttribute('aria-label', 'On this page');
      var title = document.createElement('p');
      title.className = 'toc-title';
      title.textContent = 'On this page';
      var list = document.createElement('ol');
      Array.prototype.forEach.call(headings, function (h) {
        var item = document.createElement('li');
        var link = document.createElement('a');
        link.href = '#' + h.id;
        link.textContent = h.textContent;
        item.appendChild(link);
        list.appendChild(item);
      });
      nav.appendChild(title);
      nav.appendChild(list);
      var anchor = page.querySelector('.lead') || page.querySelector('.page-title');
      anchor.parentNode.insertBefore(nav, anchor.nextSibling);
    }
  }

  // A Copy button on every code block, like the window's log panel.
  Array.prototype.forEach.call(content.querySelectorAll('pre'), function (pre) {
    var holder = document.createElement('div');
    holder.className = 'code-block';
    pre.parentNode.insertBefore(holder, pre);
    holder.appendChild(pre);
    var button = document.createElement('button');
    button.type = 'button';
    button.className = 'copy-button';
    button.textContent = 'Copy';
    button.addEventListener('click', function () {
      var text = pre.innerText.replace(/\n$/, '');
      var done = function () {
        button.textContent = 'Copied';
        window.setTimeout(function () { button.textContent = 'Copy'; }, 1500);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, function () {});
      }
    });
    holder.appendChild(button);
  });
})(document);
