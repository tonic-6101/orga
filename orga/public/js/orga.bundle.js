// Orga Bundle JS
// This file is included globally via hooks.py

frappe.provide('orga');

// Initialize Orga module
orga.init = function() {
	console.log('Orga module initialized');
};

// Call init when ready
$(document).ready(function() {
	orga.init();
});
