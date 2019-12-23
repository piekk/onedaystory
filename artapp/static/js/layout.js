window.addEventListener('load', function() {
  let today = new Date();
  let date = today.getFullYear();
  let thisYear = document.getElementById('this-year');
  thisYear.innerText = date;
})

function toggle(){
  let display = document.getElementById("sidemenu");
if (display.style.width === "0px") {
  display.style.width = "35%";
} else {
  display.style.width = "0px";
}
}
