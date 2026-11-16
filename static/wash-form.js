const paymentStatus = document.querySelector('#id_payment_status');
const receivedDate = document.querySelector('#id_payment_received_date');

if (paymentStatus && receivedDate) {
  const updateReceivedDate = () => {
    const isPaid = paymentStatus.value === 'paid';
    receivedDate.closest('.field').hidden = !isPaid;
    receivedDate.disabled = !isPaid;
    receivedDate.required = isPaid;
  };
  paymentStatus.addEventListener('change', updateReceivedDate);
  updateReceivedDate();
}
