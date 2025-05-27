-- 상담 예약 테이블
CREATE TABLE IF NOT EXISTS consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    trainer_id INTEGER NOT NULL,
    consultation_datetime TEXT NOT NULL,
    num_people INTEGER DEFAULT 1 CHECK (num_people BETWEEN 1 AND 4),
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    content TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'confirmed', 'completed', 'cancelled')),
    created_at TEXT NOT NULL,
    confirmed_at TEXT,
    cancelled_at TEXT,
    completed_at TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (trainer_id) REFERENCES trainers(id)
);

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_consultations_user_id ON consultations(user_id);
CREATE INDEX IF NOT EXISTS idx_consultations_trainer_id ON consultations(trainer_id);
CREATE INDEX IF NOT EXISTS idx_consultations_datetime ON consultations(consultation_datetime);
CREATE INDEX IF NOT EXISTS idx_consultations_status ON consultations(status);

-- 상담 후기 테이블 (상담 완료 후 작성 가능)
CREATE TABLE IF NOT EXISTS consultation_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consultation_id INTEGER NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    trainer_id INTEGER NOT NULL,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    review_text TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (consultation_id) REFERENCES consultations(id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (trainer_id) REFERENCES trainers(id)
);

-- 상담 가능 시간 설정 테이블 (트레이너별 설정)
CREATE TABLE IF NOT EXISTS trainer_schedule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trainer_id INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6), -- 0: 일요일, 6: 토요일
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    is_available BOOLEAN DEFAULT 1,
    FOREIGN KEY (trainer_id) REFERENCES trainers(id),
    UNIQUE(trainer_id, day_of_week)
);

-- 트레이너 휴무일 테이블
CREATE TABLE IF NOT EXISTS trainer_holidays (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trainer_id INTEGER NOT NULL,
    holiday_date TEXT NOT NULL,
    reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (trainer_id) REFERENCES trainers(id),
    UNIQUE(trainer_id, holiday_date)
);

-- 샘플 데이터: 트레이너 기본 스케줄 (월-토 9:00-21:00)
INSERT INTO trainer_schedule (trainer_id, day_of_week, start_time, end_time, is_available)
SELECT 
    t.id,
    d.day,
    '09:00',
    '21:00',
    CASE WHEN d.day = 0 THEN 0 ELSE 1 END -- 일요일은 휴무
FROM trainers t
CROSS JOIN (
    SELECT 0 as day UNION ALL
    SELECT 1 UNION ALL
    SELECT 2 UNION ALL
    SELECT 3 UNION ALL
    SELECT 4 UNION ALL
    SELECT 5 UNION ALL
    SELECT 6
) d
WHERE NOT EXISTS (
    SELECT 1 FROM trainer_schedule ts 
    WHERE ts.trainer_id = t.id AND ts.day_of_week = d.day
);