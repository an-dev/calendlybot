document.addEventListener("DOMContentLoaded", () => {
    // Set your publishable key: remember to change this to your live publishable key in production
    // See your keys here: https://dashboard.stripe.com/account/apikeys
    if (!('CBot' in window)) {
        return;
    }
    var stripe = Stripe(CBot.SPK);
    var checkoutSessionId = Stripe(CBot.SCid);
//
//    var createCheckoutSession = function(isAnnual = false) {
//      fetch("session-create/", {
//        method: "POST",
//        headers: {
//          "Content-Type": "application/json"
//        },
//        body: JSON.stringify({ isAnnual })
//      })
//        .then(function(result) {
//          return result.json();
//        })
//        .then(function(data) {
//          checkoutSessionId = data.checkoutSessionId;
//        });
//    };
//
//    createCheckoutSession();

//    document.querySelector("#upgrade-sm").addEventListener("click", function(evt) {
//      evt.preventDefault();
      // Initiate payment
      stripe
        .redirectToCheckout({
          sessionId: checkoutSessionId
        })
        .then(function(result) {
          console.log("error");
          // If `redirectToCheckout` fails due to a browser or network
          // error, display the localized error message to your customer
          // using `result.error.message`.
        })
        .catch(function(err) {
          console.log(err);
        });
//    });
});