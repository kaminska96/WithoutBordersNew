document.addEventListener('DOMContentLoaded', function() {
    const calendarEl = document.getElementById('calendar');
    const currentMonthEl = document.getElementById('current-month');
    const prevMonthBtn = document.getElementById('prev-month');
    const nextMonthBtn = document.getElementById('next-month');
    
    let currentDate = new Date();
    
    // Fetch orders from server
    function fetchOrders() {
        return fetch('/api/orders/')
            .then(response => response.json())
            .catch(error => {
                console.error('Error fetching orders:', error);
                return [];
            });
    }
    
    // Render calendar
    async function renderCalendar() {
        const orders = await fetchOrders();
        const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1);
        const lastDay = new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 0);
        
        currentMonthEl.textContent = new Intl.DateTimeFormat('uk-UA', { 
            month: 'long', 
            year: 'numeric' 
        }).format(currentDate);
        
        calendarEl.innerHTML = '';
        
        // Add day headers
        const days = ['Нд', 'Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб'];
        days.forEach(day => {
            const dayHeader = document.createElement('div');
            dayHeader.className = 'calendar-day-header';
            dayHeader.textContent = day;
            calendarEl.appendChild(dayHeader);
        });
        
        // Add empty cells for days before the first day of month
        const firstDayOfWeek = firstDay.getDay();
        for (let i = 0; i < firstDayOfWeek; i++) {
            const emptyDay = document.createElement('div');
            emptyDay.className = 'calendar-day other-month';
            calendarEl.appendChild(emptyDay);
        }
        
        // Add days of month
        const today = new Date();
        for (let day = 1; day <= lastDay.getDate(); day++) {
            const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
            const dayEl = document.createElement('div');
            dayEl.className = 'calendar-day';
            
            if (date.toDateString() === today.toDateString()) {
                dayEl.classList.add('today');
            }
            
            const dayHeader = document.createElement('div');
            dayHeader.className = 'calendar-day-header';
            dayHeader.textContent = day;
            dayEl.appendChild(dayHeader);
            
            // Add orders for this day
            const formattedDate = formatDateForComparison(date);
            const dayOrders = orders.filter(order => {
                const orderStart = new Date(order.planned_date);
                const orderEnd = new Date(order.estimated_end);
                return (orderStart <= date && orderEnd >= date) || 
                       formatDateForComparison(orderStart) === formattedDate || 
                       formatDateForComparison(orderEnd) === formattedDate;
            });
            
            dayOrders.forEach(order => {
                const eventEl = document.createElement('div');
                eventEl.className = 'calendar-event';
                eventEl.textContent = `${order.order_name} (${formatTime(new Date(order.planned_date))}-${formatTime(new Date(order.estimated_end))})`;
                eventEl.title = `Замовлення: ${order.order_name}\nВодій: ${order.driver || 'Не призначено'}\nТранспорт: ${order.vehicle || 'Не призначено'}`;
                dayEl.appendChild(eventEl);
            });
            
            calendarEl.appendChild(dayEl);
        }
    }
    
    // Helper functions
    function formatDateForComparison(date) {
        return date.toISOString().split('T')[0];
    }
    
    function formatTime(date) {
        return date.toLocaleTimeString('uk-UA', { hour: '2-digit', minute: '2-digit' });
    }
    
    // Event listeners
    prevMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() - 1);
        renderCalendar();
    });
    
    nextMonthBtn.addEventListener('click', () => {
        currentDate.setMonth(currentDate.getMonth() + 1);
        renderCalendar();
    });
    
    // Initial render
    renderCalendar();

        const modal = document.getElementById('order-modal');
    const closeBtn = document.querySelector('.close');
    
    // Add click handlers to all calendar events
    document.querySelectorAll('.calendar-event').forEach(event => {
        event.addEventListener('click', function() {
            const orderId = this.dataset.orderId;
            fetch(`/api/orders/${orderId}/`)
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

// document.addEventListener('DOMContentLoaded', function() {
//     const modal = document.getElementById('order-modal');
//     const closeBtn = document.querySelector('.close');
    
//     // Add click handlers to all calendar events
//     document.querySelectorAll('.calendar-event').forEach(event => {
//         event.addEventListener('click', function() {
//             const orderId = this.dataset.orderId;
//             fetch(`/api/orders/${orderId}/`)
//                 .then(response => response.json())
//                 .then(order => {
//                     document.getElementById('modal-order-name').textContent = order.name;
//                     console.log(order.starting_point);
//                     document.getElementById('modal-start-point').textContent = order.starting_point;
//                     document.getElementById('modal-destination').textContent = order.destination;
//                     document.getElementById('modal-priority').textContent = order.priority;
//                     document.getElementById('modal-status').textContent = order.status;
                    
//                     // Render products
//                     const productsList = order.order_products.map(p => 
//                         `${p.name} (${p.amount} шт., ${p.weight} кг)`
//                     ).join(', ');
//                     document.getElementById('modal-products').textContent = productsList;
                    
//                     // Render vehicles
//                     const vehiclesList = order.order_vehicles.map(v => 
//                         `${v.name} (Місткість: ${v.capacity} кг, Паливо: ${v.fuel_amount} л)`
//                     ).join(', ');
//                     document.getElementById('modal-vehicles').textContent = vehiclesList;
                    
//                     modal.style.display = 'block';
//                 })
//                 .catch(error => {
//                     console.error('Error fetching order details:', error);
//                 });
//         });
//     });
    
//     // Close modal when X is clicked
//     closeBtn.addEventListener('click', function() {
//         modal.style.display = 'none';
//     });
    
//     // Close modal when clicking outside
//     window.addEventListener('click', function(event) {
//         if (event.target == modal) {
//             modal.style.display = 'none';
//         }
//     });
// });