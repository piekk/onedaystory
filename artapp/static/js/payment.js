let y = document.getElementById('SelectPayment')

y.onchange = function(){
  let w = y.selectedIndex;
  console.log(y.options[y.selectedIndex].value);
};
