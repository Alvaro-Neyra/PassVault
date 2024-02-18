document.addEventListener("DOMContentLoaded", function() {
    var eyeicon = document.getElementsByClassName("eyeicon");
    var content = document.getElementsByClassName("password-cell-content");

    for (let i = 0; i < content.length ; i++) {
        eyeicon[i].onclick = function() {
            if (content[i].type == 'password') {
                content[i].type = 'text';
                eyeicon[i].src = '../static/images/eye-open.png';
            } else {
                content[i].type = 'password';
                eyeicon[i].src = '../static/images/eye-close.png';
            }
        }
    }
    
})

