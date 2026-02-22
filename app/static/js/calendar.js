document.addEventListener('DOMContentLoaded', async function() {
    const calendarEl = document.getElementById('calendar');
    const bookingForm = document.getElementById('bookingForm');
    const bookingModal = new bootstrap.Modal(document.getElementById('bookingModal'));
    
    // Fetch bookings and rooms
    async function fetchBookings() {
        const response = await fetch('/api/bookings');
        const bookings = await response.json();
        
        // Fetch rooms to get colors
        const roomsResponse = await fetch('/api/rooms');
        const rooms = await roomsResponse.json();
        const roomMap = rooms.reduce((acc, room) => {
            acc[room.id] = { name: room.name, color: room.color };
            return acc;
        }, {});

        return bookings.map(b => ({
            id: b.id,
            title: `${b.user_name} (${b.area}) - ${roomMap[b.room_id].name}`,
            start: `${b.date}T${b.start_time}`,
            end: `${b.date}T${b.end_time}`,
            backgroundColor: roomMap[b.room_id].color,
            borderColor: roomMap[b.room_id].color,
            extendedProps: {
                user: b.user_name,
                email: b.user_email,
                area: b.area,
                room: roomMap[b.room_id].name
            }
        }));
    }

    const initialEvents = await fetchBookings();

    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: window.innerWidth < 768 ? 'timeGridDay' : 'timeGridWeek',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: window.innerWidth < 768 ? 'timeGridDay' : 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        locale: 'es',
        slotMinTime: '05:00:00',
        slotMaxTime: '22:00:00',
        events: initialEvents,
        allDaySlot: false,
        height: 'auto',
        eventClick: function(info) {
            alert(`Reserva de: ${info.event.extendedProps.user}
Área: ${info.event.extendedProps.area}
Sala: ${info.event.extendedProps.room}
Horario: ${info.event.start.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - ${info.event.end.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}`);
        },
        dateClick: function(info) {
            // Pre-fill date when clicking a slot
            document.getElementById('booking_date').value = info.dateStr.split('T')[0];
            if (info.dateStr.includes('T')) {
                document.getElementById('start_time').value = info.dateStr.split('T')[1].substring(0, 5);
            }
            bookingModal.show();
        },
        windowResize: function(view) {
            if (window.innerWidth < 768) {
                calendar.changeView('timeGridDay');
            } else {
                calendar.changeView('timeGridWeek');
            }
        }
    });

    calendar.render();

    // Handle form submission
    bookingForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(bookingForm);
        
        try {
            const response = await fetch('/api/bookings', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (response.ok) {
                alert('¡Reserva confirmada con éxito!');
                bookingModal.hide();
                bookingForm.reset();
                // Refresh events
                const updatedEvents = await fetchBookings();
                calendar.removeAllEvents();
                calendar.addEventSource(updatedEvents);
            } else {
                alert('Error: ' + result.detail);
            }
        } catch (error) {
            console.error('Error submitting booking:', error);
            alert('Ocurrió un error al procesar la reserva.');
        }
    });
});
