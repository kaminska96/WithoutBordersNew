document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('order-modal');
    const closeBtn = document.querySelector('.close');
    
    // Add click handlers to all calendar events
    document.querySelectorAll('.calendar-event').forEach(event => {
        event.addEventListener('click', function() {
            const orderId = this.dataset.orderId;
            fetch(`/api/order/${orderId}/`)
                .then(response => response.json())
                .then(order => {
                    // Store the original order data
                    const originalOrder = JSON.parse(JSON.stringify(order));
                    
                    document.getElementById('modal-order-name').textContent = order.name;

                    const options = {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                    };

                    const plannedDate = new Date(order.planned_date);
                    const formattedPlannedDate = plannedDate.toLocaleString('uk-UA', options);

                    const estimatedEnd = new Date(order.estimated_end);
                    const formattedEstimatedEnd = estimatedEnd.toLocaleString('uk-UA', options);

                    document.getElementById('modal-time-start').textContent = 'Від ' + formattedPlannedDate;
                    document.getElementById('modal-time-end').textContent = ' до ' + formattedEstimatedEnd;
                    const warehousesText = order.warehouses.map(w => `${w.name} (${w.location})`).join(', ');
                    document.getElementById('modal-start-point').textContent = warehousesText || 'Немає складів';
                    document.getElementById('modal-priority').textContent = order.priority;
                    
                    const statusMap = {
                        0: 'Заплановано',
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

                    // Add date change functionality
                    const orderDetails = document.querySelector('.order-details');
                    
                    // Create date input and button
                    const dateChangeDiv = document.createElement('div');
                    dateChangeDiv.className = 'date-change';
                    dateChangeDiv.innerHTML = `
                        <p><strong>Змінити дату:</strong></p>
                        <input type="datetime-local" id="new-planned-date">
                        <button id="update-date-btn">Оновити дату</button>
                    `;
                    orderDetails.appendChild(dateChangeDiv);
                    
                    // Set current planned date as default value
                    const isoString = plannedDate.toISOString().slice(0, 16);
                    const pad = n => n.toString().padStart(2, '0');
                    const localString = `${plannedDate.getFullYear()}-${pad(plannedDate.getMonth() + 1)}-${pad(plannedDate.getDate())}T${pad(plannedDate.getHours())}:${pad(plannedDate.getMinutes())}`;
                    document.getElementById('new-planned-date').value = localString;
                    
                    // Add status change functionality
                    const statusChangeDiv = document.createElement('div');
                    statusChangeDiv.className = 'status-change';
                    statusChangeDiv.innerHTML = `
                        <p><strong>Змінити статус:</strong></p>
                        <select id="new-status">
                            <option value="0" ${order.status == 0 ? 'selected' : ''}>Заплановано</option>
                            <option value="1" ${order.status == 1 ? 'selected' : ''}>У дорозі</option>
                            <option value="2" ${order.status == 2 ? 'selected' : ''}>Завершено</option>
                        </select>
                        <button id="update-status-btn">Оновити статус</button>
                    `;
                    orderDetails.appendChild(statusChangeDiv);
                    
                    // Add event listener to update status button
                    document.getElementById('update-status-btn').addEventListener('click', function() {
                        const newStatus = document.getElementById('new-status').value;
                        
                        // Send update request as PUT
                        fetch(`/api/order/${orderId}/update_status/`, {
                            method: 'PUT',  // Changed from POST to PUT
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCookie('csrftoken'),
                                'X-Requested-With': 'XMLHttpRequest'  // Helps Django identify AJAX requests
                            },
                            body: JSON.stringify({ status: newStatus })
                        })
                        .then(response => {
                            if (response.ok) {
                                return response.json();
                            }
                            throw new Error('Network response was not ok');
                        })
                        .then(data => {
                            location.reload();
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert(error.message || 'Помилка при оновленні статусу');
                        });
                    });
                    
                    // Add event listener to update date button
                    document.getElementById('update-date-btn').addEventListener('click', function() {
                        const newPlannedDateStr = document.getElementById('new-planned-date').value;
                        
                        if (!newPlannedDateStr) {
                            alert('Будь ласка, виберіть коректну дату');
                            return;
                        }
                        
                        // Create a Date object from the input (this is in local time)
                        const newPlannedDate = new Date(newPlannedDateStr);
                        
                        // Calculate the duration between original planned date and estimated end
                        const originalPlannedDate = new Date(originalOrder.planned_date);
                        const originalEstimatedEnd = new Date(originalOrder.estimated_end);
                        const duration = originalEstimatedEnd - originalPlannedDate;
                        
                        // Calculate new estimated end (in local time)
                        const newEstimatedEnd = new Date(newPlannedDate.getTime() + duration);
                        
                        // Format dates for backend - include timezone offset
                        const formatForBackend = (date) => {
                            // Get timezone offset in minutes
                            const offset = date.getTimezoneOffset();
                            // Convert to hours and minutes
                            const offsetHours = Math.abs(Math.floor(offset / 60)).toString().padStart(2, '0');
                            const offsetMinutes = Math.abs(offset % 60).toString().padStart(2, '0');
                            const sign = offset > 0 ? '-' : '+';
                            
                            // Format as ISO string with timezone
                            return date.getFullYear() + '-' +
                                (date.getMonth() + 1).toString().padStart(2, '0') + '-' +
                                date.getDate().toString().padStart(2, '0') + 'T' +
                                date.getHours().toString().padStart(2, '0') + ':' +
                                date.getMinutes().toString().padStart(2, '0') + ':' +
                                date.getSeconds().toString().padStart(2, '0') +
                                sign + offsetHours + ':' + offsetMinutes;
                        };
                        
                        // Prepare data for update
                        const updateData = {
                            planned_date: formatForBackend(newPlannedDate),
                            estimated_end: formatForBackend(newEstimatedEnd)
                        };
                        
                        // Send update request
                        fetch(`/api/order/${orderId}/update_date/`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'X-CSRFToken': getCookie('csrftoken')
                            },
                            body: JSON.stringify(updateData)
                        })
                        .then(response => {
                            if (response.ok) {
                                location.reload();
                            } else {
                                throw new Error('Помилка при оновленні дати');
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert(error.message);
                        });
                    });

                    modal.style.display = 'block';
                })
                .catch(error => {
                    console.error('Error fetching order details:', error);
                });
        });
    });
    
    // Close modal when X is clicked
    closeBtn.addEventListener('click', function() {
        // Remove the added elements when closing modal
        const dateChangeDiv = document.querySelector('.date-change');
        if (dateChangeDiv) {
            dateChangeDiv.remove();
        }
        const statusChangeDiv = document.querySelector('.status-change');
        if (statusChangeDiv) {
            statusChangeDiv.remove();
        }
        modal.style.display = 'none';
    });
    
    // Close modal when clicking outside
    window.addEventListener('click', function(event) {
        if (event.target == modal) {
            // Remove the added elements when closing modal
            const dateChangeDiv = document.querySelector('.date-change');
            if (dateChangeDiv) {
                dateChangeDiv.remove();
            }
            const statusChangeDiv = document.querySelector('.status-change');
            if (statusChangeDiv) {
                statusChangeDiv.remove();
            }
            modal.style.display = 'none';
        }
    });
    
    // Function to get CSRF token
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
  document.getElementById('logoutButton').addEventListener('click', showLogoutModal);
  document.getElementById('cancelLogout').addEventListener('click', hideLogoutModal);
  
  // Prevent form submission from closing the modal
  const logoutForm = document.querySelector('#logoutModal form');
  if (logoutForm) {
    logoutForm.addEventListener('submit', function(e) {
      // Let the form submit normally
      hideLogoutModal();
    });
  }
});

function showLogoutModal() {
  const modal = document.getElementById('logoutModal');
  modal.classList.add('active');
}

function hideLogoutModal() {
  const modal = document.getElementById('logoutModal');
  modal.classList.remove('active');
}