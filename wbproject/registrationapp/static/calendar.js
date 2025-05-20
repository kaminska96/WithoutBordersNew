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
                    console.log(order.starting_point);
                    document.getElementById('modal-start-point').textContent = order.starting_point;
                    document.getElementById('modal-destination').textContent = order.destination;
                    document.getElementById('modal-priority').textContent = order.priority;
                    document.getElementById('modal-status').textContent = order.status;
                    
                    // Render products
                    const productsList = order.order_products.map(p => 
                        `${p.name} (${p.amount} шт., ${p.weight} кг)`
                    ).join(', ');
                    document.getElementById('modal-products').textContent = productsList;
                    
                    // Render vehicles
                    const vehiclesList = order.order_vehicles.map(v => 
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