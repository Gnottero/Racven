(function () {
    'use strict';

    var config = window.TV_CONFIG || {};
    var messages = (config.initialMessages || []).slice();
    var carouselIntervalMs = (config.carouselInterval || 6) * 1000;
    var messageDisplayMs = (config.messageDisplaySeconds || 8) * 1000;
    var dutyDisplayMs = (config.dutyDisplaySeconds || 15) * 1000;

    var stage = document.getElementById('tv-stage');
    var carouselEl = document.getElementById('tv-carousel');

    var carouselIndex = 0;
    var carouselTimer = null;
    var currentOverlay = null; // { type: 'message'|'duty', element, timerId }
    var eventQueue = [];

    var WEEKDAY_LABELS = ['Lun', 'Mar', 'Mer', 'Gio', 'Ven', 'Sab', 'Dom'];
    // Palette fissa di colori badge assegnati in modo deterministico per user_id,
    // cosi' la stessa persona ha sempre lo stesso colore in tutta la griglia.
    // Il rosso (--primary) e' escluso per non confondersi con lo sfondo del giorno "oggi".
    var MEMBER_COLORS = ['#2563eb', '#16a34a', '#d97706', '#7c3aed', '#0891b2', '#db2777', '#65a30d'];

    function colorForMember(userId) {
        return MEMBER_COLORS[userId % MEMBER_COLORS.length];
    }

    function formatTime(createdAt) {
        // createdAt: 'YYYY-MM-DD HH:MM:SS'
        var parts = (createdAt || '').split(' ');
        return parts.length > 1 ? parts[1].slice(0, 5) : '';
    }

    function escapeHtml(str) {
        var div = document.createElement('div');
        div.textContent = str == null ? '' : String(str);
        return div.innerHTML;
    }

    function renderCarousel() {
        if (!messages.length) {
            carouselEl.innerHTML = '<div class="tv-empty">Nessun messaggio oggi. Inviane uno dalla pagina principale!</div>';
            return;
        }
        if (carouselIndex >= messages.length) {
            carouselIndex = 0;
        }
        var m = messages[carouselIndex];
        carouselEl.innerHTML =
            '<div class="tv-carousel-card">' +
            '<div class="tv-carousel-body">&ldquo;' + escapeHtml(m.body) + '&rdquo;</div>' +
            '<div class="tv-carousel-meta">' + escapeHtml(m.first_name) + ' ' + escapeHtml(m.last_name) +
            ' &middot; ' + escapeHtml(m.user_tag) + ' &middot; ' + formatTime(m.created_at) + '</div>' +
            '</div>';
    }

    function advanceCarousel() {
        carouselIndex = (carouselIndex + 1) % Math.max(messages.length, 1);
        renderCarousel();
    }

    function startCarousel() {
        stopCarousel();
        renderCarousel();
        carouselTimer = setInterval(advanceCarousel, carouselIntervalMs);
    }

    function stopCarousel() {
        if (carouselTimer) {
            clearInterval(carouselTimer);
            carouselTimer = null;
        }
    }

    function playBeep() {
        try {
            var Ctx = window.AudioContext || window.webkitAudioContext;
            var ctx = new Ctx();
            var oscillator = ctx.createOscillator();
            var gain = ctx.createGain();
            oscillator.type = 'sine';
            oscillator.frequency.value = 880;
            gain.gain.setValueAtTime(0.0001, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.3, ctx.currentTime + 0.02);
            gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 0.5);
            oscillator.connect(gain);
            gain.connect(ctx.destination);
            oscillator.start();
            oscillator.stop(ctx.currentTime + 0.5);
            oscillator.onended = function () { ctx.close(); };
        } catch (err) {
            // AudioContext unavailable/blocked: fail silently, carousel still works.
        }
    }

    function showOverlay(html, durationMs, className, type) {
        stopCarousel();
        var overlay = document.createElement('div');
        overlay.className = className;
        overlay.innerHTML = html;
        stage.appendChild(overlay);
        var timerId = setTimeout(function () {
            overlay.classList.add('tv-fade-out');
            overlay.addEventListener('animationend', function onFadeOutEnd() {
                overlay.removeEventListener('animationend', onFadeOutEnd);
                currentOverlay = null;
                if (overlay.parentNode) {
                    stage.removeChild(overlay);
                }
                processQueue();
            });
        }, durationMs);
        currentOverlay = { type: type, element: overlay, timerId: timerId };
    }

    function showMessageOverlay(message) {
        playBeep();
        var html =
            '<div class="tv-message-tag">' + escapeHtml(message.first_name) + ' ' +
            escapeHtml(message.last_name) + ' &middot; ' + escapeHtml(message.user_tag) + '</div>' +
            '<div class="tv-message-body">&ldquo;' + escapeHtml(message.body) + '&rdquo;</div>' +
            '<div class="tv-message-time">' + formatTime(message.created_at) + '</div>';
        showOverlay(html, messageDisplayMs, 'tv-message-overlay', 'message');
    }

    function showDutyOverlay(payload) {
        var schedule = payload.schedule || { days: [] };
        var today = payload.today || { members: [] };

        var todayNames = today.members.map(function (m) {
            return m.first_name + ' ' + m.last_name + ' (' + m.user_tag + ')';
        }).join(', ') || 'Nessun contributore disponibile';

        var headerHtml = WEEKDAY_LABELS.map(function (label) {
            return '<div class="tv-duty-weekday">' + label + '</div>';
        }).join('');

        // Celle vuote per allineare il giorno 1 al reale giorno della settimana.
        var leadingBlanks = schedule.days.length ? schedule.days[0].weekday : 0;
        var blanksHtml = '';
        for (var i = 0; i < leadingBlanks; i++) {
            blanksHtml += '<div class="tv-duty-day tv-duty-day-empty"></div>';
        }

        var gridHtml = schedule.days.map(function (day) {
            var dayNumber = parseInt(day.date.split('-')[2], 10);
            var stateClass = day.is_today ? ' is-today' : (day.is_past ? ' is-past' : ' is-future');
            var membersHtml = day.members.map(function (m) {
                var initials = m.first_name[0] + m.last_name[0];
                return '<span class="tv-duty-member" style="background:' + colorForMember(m.id) + '">' +
                    escapeHtml(initials) + '</span>';
            }).join('');
            return '<div class="tv-duty-day' + stateClass + '">' +
                '<div class="day-number">' + dayNumber + '</div>' +
                '<div class="tv-duty-members">' + membersHtml + '</div>' +
                '</div>';
        }).join('');

        var html =
            '<div class="tv-duty-title">Turno piatti di oggi</div>' +
            '<div class="tv-duty-today">' + escapeHtml(todayNames) + '</div>' +
            '<div class="tv-duty-grid">' + headerHtml + blanksHtml + gridHtml + '</div>';
        showOverlay(html, dutyDisplayMs, 'tv-duty-overlay', 'duty');
    }

    // I nuovi messaggi hanno sempre priorità: saltano davanti a qualunque
    // evento "duty_display" ancora in coda, indipendentemente dall'ordine di arrivo.
    function pickNextEvent() {
        var idx = eventQueue.findIndex(function (e) { return e.type === 'chat_message'; });
        if (idx === -1) {
            idx = 0;
        }
        return eventQueue.splice(idx, 1)[0];
    }

    function processQueue() {
        if (currentOverlay || !eventQueue.length) {
            if (!currentOverlay) {
                startCarousel();
            }
            return;
        }
        var next = pickNextEvent();
        if (next.type === 'chat_message') {
            showMessageOverlay(next.data);
        } else if (next.type === 'duty_display') {
            showDutyOverlay(next.data);
        }
    }

    function enqueueEvent(type, data) {
        eventQueue.push({ type: type, data: data });
        // Un messaggio in arrivo non interrompe il turno piatti in corso: viene
        // mostrato subito dopo, quando il calendario termina il suo tempo naturale.
        if (!currentOverlay) {
            processQueue();
        }
    }

    function connectStream() {
        var source = new EventSource('/tv/stream');
        source.addEventListener('chat_message', function (evt) {
            var data = JSON.parse(evt.data);
            var exists = messages.some(function (m) { return m.id === data.id; });
            if (!exists) {
                messages.push(data);
            }
            enqueueEvent('chat_message', data);
        });
        source.addEventListener('duty_display', function (evt) {
            enqueueEvent('duty_display', JSON.parse(evt.data));
        });
    }

    startCarousel();
    connectStream();
})();
