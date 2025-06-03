window.dash_clientside = Object.assign({}, window.dash_clientside, {
    fullscreen: {
        activarPantallaCompleta: function(n_clicks) {
            const elem = document.getElementById("mapa-container");
            if (!elem) return window.dash_clientside.no_update;
            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.webkitRequestFullscreen) {
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) {
                elem.msRequestFullscreen();
            }
            return 0;
        }
    }
});
