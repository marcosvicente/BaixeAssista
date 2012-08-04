for (var index = 0; index < document.links.length; index++) {
	document.links[index].onclick = function() {
		if ( event ) {link_clicked = event.srcElement.href;}
	}
}