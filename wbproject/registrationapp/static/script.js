document.addEventListener('DOMContentLoaded', () => {
    const orderForm = document.getElementById('orderForm');
    const ordersList = document.getElementById('ordersList');
    const filterButtons = document.getElementById('filterButtons');
    const btnAll = document.getElementById('btnAll');
    const btnInPlans = document.getElementById('btnInPlans');
    const btnGoing = document.getElementById('btnGoing');
    const btnCompleted = document.getElementById('btnCompleted');
    const mapContainer = document.getElementById('map');
    let map;
    let markers = [];
  
    orderForm.addEventListener('submit', (event) => {
      event.preventDefault();
  
      const destinationInput = document.getElementById('destination');
      const destination = destinationInput.value;
  
      fetch('/orders', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded'
        },
        body: `destination=${encodeURIComponent(destination)}`
      })
        .then(() => {
          destinationInput.value = '';
          fetchOrders();
        })
        .catch((error) => {
          console.error('Error creating order:', error);
        });
    });
  
    btnAll.addEventListener('click', () => {
      filterOrders('All');
    });
  
    btnInPlans.addEventListener('click', () => {
      filterOrders('In Plans');
    });
  
    btnGoing.addEventListener('click', () => {
      filterOrders('Going');
    });
  
    btnCompleted.addEventListener('click', () => {
      filterOrders('Completed');
    });
  
    function fetchOrders() {
      fetch('/orders')
        .then((response) => response.json())
        .then((data) => {
          ordersList.innerHTML = '';
  
          data.forEach((order) => {
            const listItem = document.createElement('li');
            listItem.textContent = order.destination;
            ordersList.appendChild(listItem);
          });
  
          displayMarkers(data);
        })
        .catch((error) => {
          console.error('Error fetching orders:', error);
        });
    }
  
    function filterOrders(status) {
      const items = Array.from(ordersList.children);
  
      items.forEach((item) => {
        item.style.display = 'none';
  
        if (status === 'All' || item.dataset.status === status) {
          item.style.display = 'block';
        }
      });
  
      filterMarkers(status);
    }
  
    function displayMarkers(orders) {
      clearMarkers();
  
      orders.forEach((order) => {
        const [destination, status] = order;
  
        if (destination) {
          const geocoder = new google.maps.Geocoder();
  
          geocoder.geocode({ address: destination }, (results, status) => {
            if (status === 'OK' && results[0]) {
              const marker = new google.maps.Marker({
                position: results[0].geometry.location,
                map: map,
                title: destination
              });
  
              markers.push(marker);
            }
          });
        }
      });
    }
  
    function clearMarkers() {
      markers.forEach((marker) => {
        marker.setMap(null);
      });
  
      markers = [];
    }
  
    function filterMarkers(status) {
      markers.forEach((marker) => {
        marker.setVisible(true);
  
        if (status !== 'All') {
          const destination = marker.getTitle();
  
          if (destination) {
            const item = document.querySelector(`li[data-destination="${destination}"]`);
            if (item && item.dataset.status !== status) {
              marker.setVisible(false);
            }
          }
        }
      });
    }
  
    function initMap() {
      map = new google.maps.Map(mapContainer, {
        center: { lat: 0, lng: 0 },
        zoom: 8
      });
  
      fetchOrders();
    }
  
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=AIzaSyCUBQkyuIFqf5WE8BJn_-8BTjWV96-Hlfo&libraries=places&callback=initMap`;
    script.defer = true;
    script.async = true;
    document.head.appendChild(script);
  });
  