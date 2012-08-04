var override_open = window.open;
var link_clicked = "";

window.open = function(URL,name,specs,replace) {
	if (URL && link_clicked && link_clicked === URL) {
		return override_open(URL, name, specs, replace);
	} else {
		return false;
	}
}