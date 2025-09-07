document.addEventListener('DOMContentLoaded', function() {
    // Password strength indicator
    const passwordField = document.getElementById('password');
    if (passwordField) {
        passwordField.addEventListener('input', function() {
            const strengthIndicator = document.createElement('div');
            strengthIndicator.className = 'password-strength';
            
            if (this.value.length < 6) {
                strengthIndicator.textContent = 'Weak';
                strengthIndicator.className += ' text-danger';
            } else if (this.value.length < 10) {
                strengthIndicator.textContent = 'Medium';
                strengthIndicator.className += ' text-warning';
            } else {
                strengthIndicator.textContent = 'Strong';
                strengthIndicator.className += ' text-success';
            }
            
            const existingIndicator = document.querySelector('.password-strength');
            if (existingIndicator) {
                existingIndicator.replaceWith(strengthIndicator);
            } else {
                this.parentNode.appendChild(strengthIndicator);
            }
        });
    }
    
    // Tooltip initialization
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});