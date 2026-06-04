// Lógica del contador con micro-animaciones
document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('click-btn');
    const counterDisplay = document.getElementById('counter');
    let count = 0;

    if (button && counterDisplay) {
        button.addEventListener('click', () => {
            count++;
            counterDisplay.textContent = count;
            
            // Animación rápida de escala al hacer clic
            counterDisplay.style.transform = 'scale(1.2)';
            setTimeout(() => {
                counterDisplay.style.transform = 'scale(1)';
            }, 100);

            // Cambiar color del texto según clics
            if (count % 10 === 0) {
                counterDisplay.style.color = '#ec4899'; // Rosa
            } else if (count % 5 === 0) {
                counterDisplay.style.color = '#3b82f6'; // Azul
            } else {
                counterDisplay.style.color = '#8b5cf6'; // Morado
            }
        });
    }
});
