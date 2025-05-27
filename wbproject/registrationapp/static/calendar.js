document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('order-modal');
    const closeBtn = document.querySelector('.close');
    const fff = document.querySelectorAll('.calendar-event')
    console.log(fff);
    console.log(2);
    // Add click handlers to all calendar events
    document.querySelectorAll('.calendar-event').forEach(event => {
        event.addEventListener('click', function() {
            const orderId = this.dataset.orderId;
            console.log(orderId);
            fetch(`/api/order/${orderId}/`)
                .then(response => response.json())
                .then(order => {
                    document.getElementById('modal-order-name').textContent = order.name;
                    const warehousesText = order.warehouses.map(w => `${w.name} (${w.location})`).join(', ');
                    document.getElementById('modal-start-point').textContent = warehousesText || 'Немає складів';
                    document.getElementById('modal-priority').textContent = order.priority;
                    const statusMap = {
                        0: 'Очікує',
                        1: 'У дорозі',
                        2: 'Завершено'
                    };
                    document.getElementById('modal-status').textContent = statusMap[order.status] || 'Невідомо';

                    // Show all destinations and their products
                    let destinationInfo = '';
                    let productsInfo = '';

                    order.destinations.forEach(dest => {
                        destinationInfo += `→ ${dest.destination}\n`;

                        dest.products.forEach(p => {
                            productsInfo += `• ${p.name} (${p.amount} шт., ${p.weight} кг) — [${p.warehouse}]\n`;
                        });
                    });

                    document.getElementById('modal-destination').textContent = destinationInfo.trim();
                    document.getElementById('modal-products').textContent = productsInfo.trim();

                    // Render vehicles
                    const vehiclesList = order.vehicles.map(v => 
                        `${v.name} (Місткість: ${v.capacity} кг, Паливо: ${v.fuel_amount} л)`
                    ).join(', ');
                    document.getElementById('modal-vehicles').textContent = vehiclesList;

                    modal.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error fetching order details:', error);
                });
        });
    });
    
    // Close modal when X is clicked
    closeBtn.addEventListener('click', function() {
        modal.style.display = 'none';
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    });
});