// JavaScript for GobPrestito

// Function to show flash messages as modal
function showFlashModal(title, message, category, icon) {
    const modal = document.getElementById('flashModal');
    const modalHeader = document.getElementById('flashModalHeader');
    const modalTitle = document.getElementById('flashModalTitleText');
    const modalIcon = document.getElementById('flashModalIcon');
    const modalBody = document.getElementById('flashModalBody');
    
    // Set modal content
    modalTitle.textContent = title;
    modalBody.innerHTML = message;
    
    // Set icon
    modalIcon.className = 'bi bi-' + icon;
    
    // Set header color based on category
    const colorMap = {
        'success': 'bg-success text-white',
        'error': 'bg-danger text-white',
        'danger': 'bg-danger text-white',
        'warning': 'bg-warning text-dark',
        'info': 'bg-info text-white'
    };
    
    // Remove all color classes
    modalHeader.className = 'modal-header';
    // Add the appropriate color class
    if (colorMap[category]) {
        modalHeader.classList.add(...colorMap[category].split(' '));
    }
    
    // Show the modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
}

// Function to show confirmation modal
function showConfirmModal(button) {
    const message = button.getAttribute('data-confirm-message');
    const form = button.closest('form');
    
    const modal = document.getElementById('confirmModal');
    const modalBody = document.getElementById('confirmModalBody');
    const confirmButton = document.getElementById('confirmModalOk');
    
    // Set message
    modalBody.textContent = message;
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Handle confirmation
    confirmButton.onclick = function() {
        bsModal.hide();
        form.submit();
    };
}

// Function to show delete confirmation modal (used by various pages)
function showDeleteConfirmModal(message, action) {
    const modal = document.getElementById('confirmModal');
    const modalBody = document.getElementById('confirmModalBody');
    const confirmButton = document.getElementById('confirmModalOk');
    
    // Set message
    modalBody.textContent = message;
    
    // Show modal
    const bsModal = new bootstrap.Modal(modal);
    bsModal.show();
    
    // Handle confirmation
    confirmButton.onclick = function() {
        bsModal.hide();
        if (typeof action === 'function') {
            action();
        }
    };
}

document.addEventListener('DOMContentLoaded', function() {
    // Form validation enhancement
    const forms = document.querySelectorAll('form[method="POST"]');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            // Check if form is valid
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Search form auto-submit on checkbox change
    const searchCheckboxes = document.querySelectorAll('input[type="checkbox"][name="disponibili"]');
    searchCheckboxes.forEach(function(checkbox) {
        checkbox.addEventListener('change', function() {
            this.closest('form').submit();
        });
    });

    // Highlight active navigation items
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    navLinks.forEach(function(link) {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });

    // Add loading indicator to forms on submit
    forms.forEach(function(form) {
        form.addEventListener('submit', function() {
            if (form.classList.contains('no-loading')) {
                return;
            }
            const submitButton = form.querySelector('button[type="submit"]');
            if (submitButton) {
                submitButton.disabled = true;
                submitButton.innerHTML = '<span class="loading"></span> Attendere...';
            }
        });
    });

    // Table row click to expand details
    const tableRows = document.querySelectorAll('table tbody tr[data-toggle="details"]');
    tableRows.forEach(function(row) {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function() {
            const detailsRow = this.nextElementSibling;
            if (detailsRow && detailsRow.classList.contains('details-row')) {
                detailsRow.classList.toggle('d-none');
            }
        });
    });

    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
});

// Utility function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
}

// Utility function to calculate days between dates
function daysBetween(date1, date2) {
    const oneDay = 24 * 60 * 60 * 1000;
    const firstDate = new Date(date1);
    const secondDate = new Date(date2);
    return Math.round(Math.abs((firstDate - secondDate) / oneDay));
}

// Console message
console.log('%c🎲 Il Sentiero dei Draghi - Sistema Gestione Prestiti Giochi da Tavolo', 'color: #0d6efd; font-size: 16px; font-weight: bold;');
