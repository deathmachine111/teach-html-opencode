/* teach-html — sidebar TOC scrollspy + reading progress. Vanilla, no deps. */
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

  // progress checkboxes (localStorage) — toggled by clicking a heading
  try{ var saved = JSON.parse(localStorage.getItem('teach-progress')||'{}'); }catch(e){ saved={}; }
  ids.forEach(function(id){
    var o = byId[id];
    if(saved[id]) o.el.classList.add('read');
    o.el.addEventListener('click', function(){
      o.el.classList.toggle('read');
      saved[id] = o.el.classList.contains('read');
      try{ localStorage.setItem('teach-progress', JSON.stringify(saved)); }catch(e){}
    });
  });
})();
