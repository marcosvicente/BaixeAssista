var old_open = window.open
var clickedEvent = false
var clickedLink = ""

document.onclick = function() {
 clickedLink = event.srcElement.href
 clickedEvent = true
}

window.open = function(URL, name, specs, replace) {
	if (URL && clickedLink && clickedLink == URL && clickedEvent == true) {
		clickedEvent = false; return old_open(URL, name, specs, replace);
	} else {
		return false
	}
}