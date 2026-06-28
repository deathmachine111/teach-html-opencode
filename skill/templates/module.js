/* teach-html-opencode — sidebar TOC scrollspy + reading progress.
 * Vanilla, no deps. Tracks "read" state in localStorage and shows a small
 * green check next to visited items in the TOC.
 */
(function(){
  var links = Array.prototype.slice.call(document.querySelectorAll('.toc-nav a'));
  if(!links.length) return;
  var byId = {};
  links.forEach(function(l){
    var id = l.getAttribute('href').slice(1);
    var el = document.getElementById(id);
    if(el) byId[id] = {link:l, el:el};
  });
  var ids = Object.keys(byId);

  function onScroll(){
    var pos = window.scrollY + 80;
    var active = null;
    for(var i=0;i<ids.length;i++){
      var o = byId[ids[i]];
      if(o.el.offsetTop <= pos) active = ids[i];
    }
    links.forEach(function(l){ l.classList.remove('active'); });
    if(active && byId[active]) byId[active].link.classList.add('active');
  }

  var ticking = false;
  window.addEventListener('scroll', function(){
    if(!ticking){ window.requestAnimationFrame(function(){ onScroll(); ticking=false; }); ticking=true; }
  });
  onScroll();

  // reading progress (localStorage) — click any heading to toggle "read"
  try{ var saved = JSON.parse(localStorage.getItem('teach-progress')||'{}'); }catch(e){ saved={}; }
  ids.forEach(function(id){
    var o = byId[id];
    function paint(){
      var isRead = !!saved[id];
      o.el.classList.toggle('read', isRead);
      o.link.classList.toggle('read', isRead);
      if(isRead && !o.link.querySelector('.toc-check')){
        var ck = document.createElement('span');
        ck.className = 'toc-check';
        ck.textContent = '✓';
        ck.setAttribute('aria-label','read');
        o.link.appendChild(ck);
      } else if(!isRead && o.link.querySelector('.toc-check')){
        o.link.querySelector('.toc-check').remove();
      }
    }
    paint();
    o.el.addEventListener('click', function(){
      saved[id] = !o.el.classList.contains('read');
      o.el.classList.toggle('read');
      paint();
      try{ localStorage.setItem('teach-progress', JSON.stringify(saved)); }catch(e){}
    });
  });
})();
