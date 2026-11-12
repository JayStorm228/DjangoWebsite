/*!
 * TRShop — небольшие улучшения поверх Bootstrap.
 */
window.addEventListener("DOMContentLoaded", () => {
    const navbar = document.getElementById("mainNav");

    // На внутренних страницах шапка изначально светлая и такой остаётся.
    const solidNavbar = Boolean(navbar && navbar.classList.contains("navbar-shrink"));

    const shrinkNavbar = () => {
        if (!navbar || solidNavbar) {
            return;
        }
        navbar.classList.toggle("navbar-shrink", window.scrollY > 40);
    };

    if (navbar) {
        shrinkNavbar();
        document.addEventListener("scroll", shrinkNavbar, { passive: true });
    }

    // Закрываем мобильное меню после выбора пункта.
    const toggler = document.querySelector(".navbar-toggler");
    document.querySelectorAll("#navbarResponsive .nav-link").forEach((link) => {
        link.addEventListener("click", () => {
            if (toggler && window.getComputedStyle(toggler).display !== "none") {
                toggler.click();
            }
        });
    });
});
