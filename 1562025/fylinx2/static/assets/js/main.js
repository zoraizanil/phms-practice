const loginBtn = document.getElementById("show-login");
const loginBox = document.getElementById("login-box");
const signupBtn = document.getElementById("show-signup");
const signupBox = document.getElementById("signup-box");
const loginForm = document.getElementById("login-form");
const signupForm = document.getElementById("signup-form");

// Show login box
loginBtn.addEventListener("click", function (e) {
  e.preventDefault();
  loginBox.style.display = "block";
});

// Hide login box when clicking outside
document.addEventListener("click", function (e) {
  if (
    loginBox.style.display === "block" &&
    !loginBox.contains(e.target) &&
    e.target !== loginBtn
  ) {
    loginBox.style.display = "none";
  }
});

// Submitted Form

// Submitted Form - Updated
loginForm.addEventListener("submit", function (e) {
  if (!loginForm.checkValidity()) {
    e.preventDefault(); // prevent submission only if the form is invalid
  }
});


// Login-Form Animation

 document.getElementById("show-login").addEventListener("click", function (e) {
    e.preventDefault();
    const loginBox = document.getElementById("login-box");

    // Reset animation
    loginBox.classList.remove("animate");
    loginBox.style.display = "none";

    // Force reflow
    void loginBox.offsetWidth;

    // Trigger animation again
    loginBox.style.display = "block";
    setTimeout(() => {
      loginBox.classList.add("animate");
    }, 10); // small delay to trigger transition
  });


  // functionalities
(function() {
  "use strict";

 

  /**
   * Mobile nav toggle
   */
  const mobileNavToggleBtn = document.querySelector('.mobile-nav-toggle');

  function mobileNavToogle() {
    document.querySelector('body').classList.toggle('mobile-nav-active');
    mobileNavToggleBtn.classList.toggle('bi-list');
    mobileNavToggleBtn.classList.toggle('bi-x');
  }
  mobileNavToggleBtn.addEventListener('click', mobileNavToogle);

  /**
   * Preloader
   */
  const preloader = document.querySelector('#preloader');
  if (preloader) {
    window.addEventListener('load', () => {
      preloader.remove();
    });
  }

  /**
   * Scroll top button
   */
  let scrollTop = document.querySelector('.scroll-top');

  function toggleScrollTop() {
    if (scrollTop) {
      window.scrollY > 100 ? scrollTop.classList.add('active') : scrollTop.classList.remove('active');
    }
  }
  scrollTop.addEventListener('click', (e) => {
    e.preventDefault();
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  });

  window.addEventListener('load', toggleScrollTop);
  document.addEventListener('scroll', toggleScrollTop);

  /**
   * Navmenu Scrollspy
   */
  let navmenulinks = document.querySelectorAll('.navmenu a');

  function navmenuScrollspy() {
    navmenulinks.forEach(navmenulink => {
      if (!navmenulink.hash) return;
      let section = document.querySelector(navmenulink.hash);
      if (!section) return;
      let position = window.scrollY + 200;
      if (position >= section.offsetTop && position <= (section.offsetTop + section.offsetHeight)) {
        document.querySelectorAll('.navmenu a.active').forEach(link => link.classList.remove('active'));
        navmenulink.classList.add('active');
      } else {
        navmenulink.classList.remove('active');
      }
    })
  }
  window.addEventListener('load', navmenuScrollspy);
  document.addEventListener('scroll', navmenuScrollspy);

})();