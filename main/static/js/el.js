var source_url = "";
var ptrSearchURL = 0;
var clickedLink = "";
var alive_time_count = 0;
var pattern = /http:\/\/moevideo\.net\/video\.php\?file=\w+\.\w+/;

ptrSearchURL = setInterval(function () {
    var script_tags = document.getElementsByTagName("script");
    if (script_tags) {
        for (var i = 0; i < script_tags.length; i++) {
            source_url = script_tags[i].src;

            if (pattern.test(source_url)) {
                clickedLink = source_url;
                clickedEvent = true;
                window.open(source_url);
                clearInterval(ptrSearchURL);
            }
        }
        if (alive_time_count > 5) {
            clearInterval(ptrSearchURL);
        }
    }
    alive_time_count++;
}, 1000);