// Year in footer
const currentYear = new Date().getFullYear()
const yearSpan = document.getElementById("year")
yearSpan.setAttribute("datetime", currentYear)
yearSpan.textContent = currentYear


// Greeter in index.html
var greetSpan = document.getElementById("greeter")
var currentHour = new Date().getHours()
var greetMessage
if (currentHour > 12) {
    greetMessage = "Aftenoon"
} else if (currentHour > 18) {
    greetMessage = "Evening"
} else {
    greetMessage = "Morning"
}
greetSpan.textContent = greetMessage