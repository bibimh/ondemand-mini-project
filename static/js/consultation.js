// 날짜 선택기 초기화
const dateInput = document.getElementById('consultation_date');
const availableTimesDiv = document.getElementById('availableTimes');
const timeSlotsContainer = document.querySelector('.time-slots');

// Flatpickr 날짜 선택기 설정
flatpickr(dateInput, {
    locale: "ko",
    minDate: "today",
    maxDate: new Date().fp_incr(30), // 30일 후까지만 예약 가능
    disable: [
        function(date) {
            // 일요일 비활성화
            return (date.getDay() === 0);
        }
    ],
    onChange: function(selectedDates, dateStr, instance) {
        if (selectedDates.length > 0) {
            loadAvailableTimes(dateStr);
        }
    }
});

// 선택한 날짜의 가능한 시간대 로드
function loadAvailableTimes(date) {
    // 실제로는 서버에서 해당 날짜의 예약 가능한 시간을 가져와야 함
    // 여기서는 예시로 시간대를 생성
    const times = [
        '09:00', '10:00', '11:00', '12:00',
        '14:00', '15:00', '16:00', '17:00',
        '18:00', '19:00', '20:00', '21:00'
    ];
    
    // 예약된 시간 (서버에서 가져와야 함)
    const bookedTimes = ['10:00', '15:00', '19:00'];
    
    timeSlotsContainer.innerHTML = '';
    
    times.forEach(time => {
        const timeSlot = document.createElement('div');
        timeSlot.className = 'time-slot';
        timeSlot.textContent = time;
        
        if (bookedTimes.includes(time)) {
            timeSlot.classList.add('disabled');
        } else {
            timeSlot.addEventListener('click', function() {
                selectTimeSlot(this);
            });
        }
        
        timeSlotsContainer.appendChild(timeSlot);
    });
    
    availableTimesDiv.style.display = 'block';
}

// 시간대 선택
function selectTimeSlot(slot) {
    if (slot.classList.contains('disabled')) return;
    
    // 기존 선택 제거
    document.querySelectorAll('.time-slot.selected').forEach(s => {
        s.classList.remove('selected');
    });
    
    // 새로운 선택
    slot.classList.add('selected');
}

// 전화번호 자동 포맷팅
const phoneInput = document.getElementById('phone');
phoneInput.addEventListener('input', function(e) {
    let value = e.target.value.replace(/[^0-9]/g, '');
    
    if (value.length >= 3 && value.length < 7) {
        value = value.slice(0, 3) + '-' + value.slice(3);
    } else if (value.length >= 7) {
        value = value.slice(0, 3) + '-' + value.slice(3, 7) + '-' + value.slice(7, 11);
    }
    
    e.target.value = value;
});

// 폼 제출 처리
document.getElementById('consultationForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    // 시간 선택 확인
    const selectedTime = document.querySelector('.time-slot.selected');
    if (!selectedTime) {
        alert('상담 시간을 선택해주세요.');
        return;
    }
    
    // 폼 데이터 수집
    const formData = new FormData(this);
    formData.append('consultation_time', selectedTime.textContent);
    
    // 실제로는 서버로 전송
    fetch('/api/consultation', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('상담 신청이 완료되었습니다.\n확인 문자를 발송해드렸습니다.');
            window.location.href = '/';
        } else {
            alert('상담 신청 중 오류가 발생했습니다.\n다시 시도해주세요.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('상담 신청 중 오류가 발생했습니다.');
    });
});