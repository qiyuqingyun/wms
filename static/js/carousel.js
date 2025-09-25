(function(){
  function initCarousel(root){
    const track = root.querySelector('[data-carousel-track]');
    const slides = Array.from(track.children);
    const prev = root.querySelector('[data-carousel-prev]');
    const next = root.querySelector('[data-carousel-next]');
    if (!slides.length) return;
    let index = 0;
    function update(){
      slides.forEach((s,i)=>{
        s.classList.toggle('active', i === index);
      });
      const slideWidth = slides[0].getBoundingClientRect().width + 16; // include gap
      const containerWidth = root.getBoundingClientRect().width;
      const offset = (containerWidth/2) - (slideWidth/2) - (index * slideWidth);
      track.style.transform = `translateX(${offset}px)`;
    }
    prev && prev.addEventListener('click', ()=>{ index = (index - 1 + slides.length) % slides.length; update(); });
    next && next.addEventListener('click', ()=>{ index = (index + 1) % slides.length; update(); });
    // wheel for fun
    root.addEventListener('wheel', (e)=>{ e.preventDefault(); if (e.deltaY > 0) { index = (index + 1) % slides.length; } else { index = (index - 1 + slides.length) % slides.length; } update(); }, {passive:false});
    // drag support
    let startX=null;
    track.addEventListener('pointerdown', (e)=>{ startX = e.clientX; track.setPointerCapture(e.pointerId); });
    track.addEventListener('pointerup', (e)=>{ if (startX==null) return; const dx = e.clientX - startX; if (Math.abs(dx)>30){ if (dx<0) index=(index+1)%slides.length; else index=(index-1+slides.length)%slides.length; } startX = null; update(); });
    window.addEventListener('resize', update);
    update();
  }
  document.addEventListener('DOMContentLoaded', ()=>{
    document.querySelectorAll('[data-carousel]').forEach(initCarousel);
  });
})();

