document.addEventListener("DOMContentLoaded", () => {
    // Set your publishable key: remember to change this to your live publishable key in production
    // See your keys here: https://dashboard.stripe.com/account/apikeys
    var stripe = Stripe('pk_test_ok6aS8NQwE5J1wpV3Oa7n2Qu00fzNa95ch');
    var checkoutSessionId = null;

    var createCheckoutSession = function(isAnnual = false) {
      fetch("session-create/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ isAnnual })
      })
        .then(function(result) {
          return result.json();
        })
        .then(function(data) {
          checkoutSessionId = data.checkoutSessionId;
        });
    };

    document.querySelector("#submit").addEventListener("click", function(evt) {
      evt.preventDefault();
      createCheckoutSession();
      debugger;
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
    });
});