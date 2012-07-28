var srcUrl = ""; var alive_time = 0;
var pattern = /http:\/\/moevideo\.net\/video\.php\?file=\w+\.\w+/;

var ptrSearchURL = setInterval(function() {
	var scriptTags = document.getElementsByTagName("script");
	
	if ( scriptTags ) {
		for (var i=0; i < scriptTags.length; i++) {
			srcUrl = scriptTags[i].src;
			
			if (pattern.test( srcUrl )) {
				window.location = srcUrl;
				clearInterval( ptrSearchURL );
			}
		}
		
		if (alive_time > 5) {
			clearInterval( ptrSearchURL );
		}
	}
	alive_time++;
}, 1000);