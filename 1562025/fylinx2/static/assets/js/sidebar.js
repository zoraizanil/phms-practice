function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  sidebar.classList.toggle("collapsed");
}

function toggleSubmenu(id, element) {
  const submenus = document.querySelectorAll(".nav > li > ul");
  const icons = document.querySelectorAll(".nav-link i");

  submenus.forEach((menu) => {
    if (menu.id !== id) {
      menu.classList.add("d-none");
    }
  });

  icons.forEach((icon) => {
    icon.classList.remove("rotate-down");
  });

  const submenu = document.getElementById(id);
  submenu.classList.toggle("d-none");

  const icon = element.querySelector(".bi-caret-right-fill");
  if (!submenu.classList.contains("d-none")) {
    icon.classList.add("rotate-down");
  } else {
    icon.classList.remove("rotate-down");
  }
}

function loadPage(url) {
  fetch(url)
    .then((response) => {
      if (!response.ok) throw new Error("Page not found");
      return response.text();
    })
    .then((html) => {
      document.getElementById("content-area").innerHTML = html;

      // ✅ Re-run dropdown logic after content is injected
      initPharmacyDropdowns();
    })
    .catch((error) => {
      document.getElementById("content-area").innerHTML =
        "<h3>Page not found.</h3>";
    });
}

// ✅ Dropdown logic in separate function so it can be reused
function initPharmacyDropdowns() {
  const dropdownConfigs = [
    {
      buttonSelector: "#manager-form .dropdown-toggle",
      menuSelector: "#manager-Dropdown",
      inputType: "checkbox",
      placeholder: "Select Pharmacy",
    },
    {
      buttonSelector: "#staff-form .dropdown-toggle",
      menuSelector: "#staff-Dropdown",
      inputType: "radio",
      placeholder: "Select Pharmacy",
    },
  ];

  dropdownConfigs.forEach((config) => {
    const dropdownButton = document.querySelector(config.buttonSelector);
    const dropdownMenu = document.querySelector(config.menuSelector);

    if (!dropdownButton || !dropdownMenu) {
      return;
    }

    let pharmaciesLoaded = false;

    dropdownButton.addEventListener("click", function () {
      if (pharmaciesLoaded) return;

      fetch("/pharmacy/api/pharmacies/")
        .then((response) => {
          if (!response.ok) throw new Error("Network response was not ok");
          return response.json();
        })
        .then((data) => {
          dropdownMenu.innerHTML = "";

          if (!data.length) {
            dropdownMenu.innerHTML = "<li>No pharmacies found</li>";
            return;
          }

          data.forEach((pharmacy) => {
            const item = document.createElement("li");
            item.innerHTML = `
              <label>
                <input type="${config.inputType}" name="${
              config.inputType === "radio" ? "staff_pharmacy" : "pharmacies[]"
            }" value="${pharmacy.id}">
                ${pharmacy.name}
              </label>
            `;
            dropdownMenu.appendChild(item);
          });

          dropdownMenu.addEventListener("click", (e) => e.stopPropagation());

          dropdownMenu.addEventListener("change", () => {
            let selectedLabels = [];

            if (config.inputType === "checkbox") {
              selectedLabels = Array.from(
                dropdownMenu.querySelectorAll("input[type='checkbox']:checked")
              ).map((input) => input.parentElement.textContent.trim());
            } else {
              const selectedRadio = dropdownMenu.querySelector(
                "input[type='radio']:checked"
              );
              selectedLabels = selectedRadio
                ? [selectedRadio.parentElement.textContent.trim()]
                : [];
            }

            dropdownButton.textContent = selectedLabels.length
              ? selectedLabels.join(", ")
              : config.placeholder;
          });

          pharmaciesLoaded = true;
        })
        .catch((error) => {
          console.error("Error fetching pharmacies:", error);
        });
    });
  });
}

// ✅ Initial run for first load
document.addEventListener("DOMContentLoaded", initPharmacyDropdowns);

// load pharmacies dynamically in pharmacy tab...

function toggleSubmenu(submenuId, element) {
  const submenu = document.getElementById(submenuId);
  submenu.classList.toggle("d-none");
  element.querySelector(".bi-caret-right-fill")?.classList.toggle("rotate-90");
}

// Dynamically load pharmacies
function loadPharmacies() {
  const submenu = document.getElementById("pharmacies-submenu");
  submenu.innerHTML =
    "<li class='nav-item'><span class='nav-link'>Loading...</span></li>";

  fetch("/pharmacy/api/pharmacies/") // Replace with actual endpoint
    .then((response) => response.json())
    .then((data) => {
      if (Array.isArray(data) && data.length > 0) {
        submenu.innerHTML = "";
        data.forEach((pharmacy) => {
          const li = document.createElement("li");
          li.className = "nav-item";

          li.innerHTML = `
                        <a class="nav-link d-flex align-items-center" onclick="togglePharmacySubmenu(${pharmacy.id}, this)">
                            <i class="bi bi-shop"></i>
                            <span class="nav-text">${pharmacy.name}</span>
                            <i class="bi bi-caret-right-fill ms-auto text-white nav-text"></i>
                        </a>
                        <ul id="submenu-${pharmacy.id}" class="nav flex-column ms-3 d-none"></ul>
                    `;

          submenu.appendChild(li);
        });
      } else {
        submenu.innerHTML =
          "<li class='nav-item'><span class='nav-link'>No pharmacies found</span></li>";
      }
    })
    .catch((error) => {
      console.error("Error loading pharmacies:", error);
      submenu.innerHTML =
        "<li class='nav-item'><span class='nav-link text-danger'>Error loading data</span></li>";
    });
}

function togglePharmacySubmenu(pharmacyId, clickedElement) {
  const submenu = document.getElementById(`submenu-${pharmacyId}`);
  submenu.classList.toggle("d-none");

  // Sirf pehli dafa submenu items load karo
  if (submenu.children.length === 0) {
    submenu.innerHTML = `
            <li class="nav-item">
                <a class="nav-link" onclick="loadPage('pharmacy/${pharmacyId}/inventory')">Inventory</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" onclick="loadPage('pharmacy/${pharmacyId}/sales')">Sales</a>
            </li>
            <li class="nav-item">
                <a class="nav-link" onclick="loadPage('pharmacy/${pharmacyId}/manager')">See Manager</a>
            </li>
        `;
  }
}



