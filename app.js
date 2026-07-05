/*
==========================================================
Web Scraping & Data Extraction System
Premium JavaScript
Part 6A
==========================================================
*/

document.addEventListener("DOMContentLoaded", () => {

    initializeNavbar();

    initializeScrapeForm();

    initializeAlerts();

    initializeScrollButton();

    initializeCards();

});

/*==========================================================
Navbar Active Link
==========================================================*/

function initializeNavbar() {

    const currentPath = window.location.pathname;

    document.querySelectorAll(".navbar .nav-link")
        .forEach(link => {

            const href = link.getAttribute("href");

            if (!href) return;

            if (
                currentPath === href ||
                (href !== "/" && currentPath.startsWith(href))
            ) {
                link.classList.add("active");
            }

        });

}

/*==========================================================
Scrape Form
==========================================================*/

function initializeScrapeForm() {

    const form = document.querySelector(
        'form[action*="scrape"]'
    );

    if (!form) return;

    const input = form.querySelector(
        'input[name="url"]'
    );

    const button = form.querySelector(
        'button[type="submit"]'
    );

    form.addEventListener("submit", function (event) {

        const value = input.value.trim();

        if (!validateURL(value)) {

            event.preventDefault();

            showMessage(
                "Please enter a valid website URL.",
                "warning"
            );

            input.focus();

            return;

        }

        button.disabled = true;

        button.classList.add("btn-loading");

        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2"></span>
            Scraping...
        `;

    });

}

/*==========================================================
URL Validation
==========================================================*/

function validateURL(url) {

    try {

        const parsed = new URL(url);

        return (
            parsed.protocol === "http:" ||
            parsed.protocol === "https:"
        );

    }

    catch {

        return false;

    }

}

/*==========================================================
Flash Alerts
==========================================================*/

function initializeAlerts() {

    const alerts =
        document.querySelectorAll(".alert");

    alerts.forEach(alert => {

        setTimeout(() => {

            const bsAlert =
                bootstrap.Alert.getOrCreateInstance(alert);

            bsAlert.close();

        }, 4500);

    });

}

/*==========================================================
Toast Message
==========================================================*/

function showMessage(message, type = "info") {

    const alert = document.createElement("div");

    alert.className =
        `alert alert-${type} position-fixed`;

    alert.style.top = "100px";
    alert.style.right = "20px";
    alert.style.zIndex = "99999";
    alert.style.minWidth = "320px";

    alert.innerHTML = `
        <strong>${message}</strong>
    `;

    document.body.appendChild(alert);

    setTimeout(() => {

        alert.remove();

    }, 3500);

}

/*==========================================================
Scroll Button
==========================================================*/

function initializeScrollButton() {

    const button =
        document.getElementById("scrollTop");

    if (!button) return;

    window.addEventListener("scroll", () => {

        if (window.scrollY > 250) {

            button.style.display = "flex";

        }

        else {

            button.style.display = "none";

        }

    });

}

/*==========================================================
Scroll To Top
==========================================================*/

function scrollToTop() {

    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}

/*==========================================================
Card Animation
==========================================================*/

function initializeCards() {

    const cards =
        document.querySelectorAll(".glass-card");

    cards.forEach((card, index) => {

        card.style.animationDelay =
            `${index * 0.08}s`;

    });

}
/*==========================================================
Export Buttons
==========================================================*/

function initializeExportButtons() {

    document.querySelectorAll(".btn-export")
        .forEach(button => {

            button.addEventListener("click", function () {

                this.classList.add("btn-loading");

                const originalHTML = this.innerHTML;

                this.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2"></span>
                    Exporting...
                `;

                setTimeout(() => {

                    this.classList.remove("btn-loading");

                    this.innerHTML = originalHTML;

                }, 2500);

            });

        });

}

/*==========================================================
Delete Confirmation
==========================================================*/

function initializeDeleteButtons() {

    document.querySelectorAll(".btn-delete")
        .forEach(button => {

            button.addEventListener("click", function (event) {

                const confirmed = confirm(
                    "Are you sure you want to delete this record?"
                );

                if (!confirmed) {

                    event.preventDefault();

                }

            });

        });

}

/*==========================================================
Premium Table Hover
==========================================================*/

function initializeTableEffects() {

    document.querySelectorAll(".premium-table tbody tr")
        .forEach(row => {

            row.addEventListener("mouseenter", () => {

                row.style.transition = ".25s";

            });

        });

}

/*==========================================================
Ripple Effect
==========================================================*/

function initializeRippleButtons() {

    document.querySelectorAll(".btn")
        .forEach(button => {

            button.addEventListener("click", function (event) {

                const ripple = document.createElement("span");

                const rect = this.getBoundingClientRect();

                ripple.style.position = "absolute";
                ripple.style.borderRadius = "50%";
                ripple.style.pointerEvents = "none";
                ripple.style.background = "rgba(255,255,255,.45)";
                ripple.style.width = "20px";
                ripple.style.height = "20px";
                ripple.style.left = `${event.clientX - rect.left - 10}px`;
                ripple.style.top = `${event.clientY - rect.top - 10}px`;
                ripple.style.transform = "scale(0)";
                ripple.style.transition = "transform .5s, opacity .5s";
                ripple.style.opacity = "1";

                this.appendChild(ripple);

                requestAnimationFrame(() => {

                    ripple.style.transform = "scale(15)";
                    ripple.style.opacity = "0";

                });

                setTimeout(() => {

                    ripple.remove();

                }, 600);

            });

        });

}

/*==========================================================
Accordion Enhancement
==========================================================*/

function initializeAccordion() {

    document.querySelectorAll(".accordion-button")
        .forEach(button => {

            button.addEventListener("click", () => {

                button.blur();

            });

        });

}

/*==========================================================
Image Animation
==========================================================*/

function initializeImages() {

    document.querySelectorAll("img")
        .forEach(image => {

            image.loading = "lazy";

        });

}

/*==========================================================
Window Load
==========================================================*/

window.addEventListener("load", () => {

    initializeExportButtons();

    initializeDeleteButtons();

    initializeTableEffects();

    initializeRippleButtons();

    initializeAccordion();

    initializeImages();

});

/*==========================================================
Keyboard Shortcut
Ctrl + /
Focus URL Input
==========================================================*/

document.addEventListener("keydown", function (event) {

    if (event.ctrlKey && event.key === "/") {

        event.preventDefault();

        const input = document.querySelector(
            'input[name="url"]'
        );

        if (input) {

            input.focus();

        }

    }

});

/*==========================================================
Console Banner
==========================================================*/

console.log(`
=========================================
Web Scraping & Data Extraction System
Developed by Ayush Yadav
Python • Flask • BeautifulSoup • MySQL
=========================================
`);