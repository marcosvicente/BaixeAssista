window.new_open = window.open // guarda para quando um link for clicado, nao uma popup
var link_clicked = "";

window.open = function(URL,name,specs,replace) {
	if (URL && link_clicked && link_clicked === URL) {
		return window.new_open(URL, name, specs, replace);
	} else {
		return false;
	}
}

for (var index = 0; index < document.links.length; index++) {
	document.links[index].onclick = function() {
		if ( event ) {link_clicked = event.srcElement.href;}
	}
}