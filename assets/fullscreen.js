window.dash_clientside = Object.assign({}, window.dash_clientside, {
    fullscreen: {
        activarPantallaCompleta: function(n_clicks) {
            const elem = document.getElementById("mapa-container");
            if (!elem) return window.dash_clientside.no_update;

            function requestFull(el) {
                if (el.requestFullscreen) {
                    el.requestFullscreen();
                } else if (el.webkitRequestFullscreen) {
                    el.webkitRequestFullscreen();
                } else if (el.msRequestFullscreen) {
                    el.msRequestFullscreen();
                }
            }

            requestFull(elem);

            setTimeout(() => {
                window.dispatchEvent(new Event('resize'));
            }, 1000);

            return 0;
        }
    }
});
