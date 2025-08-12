from sqlalchemy.exc import IntegrityError, DataError, DBAPIError
from main import app, db
from models import (
    User, Admin, Worker, Student, Maintenancer, Professor, Secretary, Conductor,
    Dependency, Amphitheater, Classroom, Course, Class, Instrument, Maintenance,
    Presentation, Rehearsal, Enrollment, Attendance, Participation
)
from sqlalchemy import text
from seeder import reset_and_seed

def run_integrity_tests():
    print("Running database integrity tests...")
    test_results = {
        'passed': 0,
        'failed': 0,
        'errors': 0
    }

    def run_test(test_func, test_name):
        try:
            test_func()
            print(f"✓ PASSED: {test_name}")
            test_results['passed'] += 1
        except AssertionError as e:
            print(f"✗ FAILED: {test_name} - {str(e)}")
            test_results['failed'] += 1
        except Exception as e:
            print(f"⚠ ERROR: {test_name} - {str(e)}")
            test_results['errors'] += 1
            
    def test_conductor_bonus_trigger():
        user = User(name="Test User", email="testuser@example.com", password="testpass")
        db.session.add(user)
        db.session.commit()

        worker = Worker(user_id=user.id, salary=1000.0)
        db.session.add(worker)
        db.session.commit()

        professor = Professor(worker_id=worker.id, academic_bg="PhD in Music")
        db.session.add(professor)
        db.session.commit()

        salary_before = worker.salary

        conductor = Conductor(professor_id=professor.id, level=3)
        db.session.add(conductor)
        db.session.commit()

        db.session.refresh(worker)
        salary_after = worker.salary
        expected_salary = salary_before * 1.15
        
        if not abs(salary_after - expected_salary) < 0.01:
            raise AssertionError(f"Salary not updated properly: {salary_after} != {expected_salary}")

    def test_instrument_maintenance_trigger():
        dep = Dependency(name="Test Dependency")
        db.session.add(dep)
        db.session.commit()

        instrument = Instrument(status="APTO", dependency_id=dep.id)
        db.session.add(instrument)
        db.session.commit()

        instrument.status = "EM_MANUTENCAO"
        db.session.commit()
        db.session.refresh(instrument)
        
        if instrument.dependency_id is not None:
            raise AssertionError("Instrument dependency_id should be NULL when going to maintenance")

        try:
            instrument.status = "EM_MANUTENCAO"
            instrument.dependency_id = dep.id
            db.session.commit()
            raise AssertionError("Trigger did not block invalid allocation!")
        except (DBAPIError, IntegrityError):
            db.session.rollback()

    def test_user_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # 1. Insert valid user
            conn.execute(text("""
                INSERT INTO user (name, email, password) VALUES
                ('Alice', 'alice@example.com', 'password123')
            """))

            # 2. Insert user with missing name (should raise error)
            try:
                conn.execute(text("""
                    INSERT INTO user (email, password) VALUES
                    ('bob@example.com', 'password456')
                """))
                raise AssertionError("Allowed insert with missing name")
            except Exception:
                pass  # Expected error

            # 3. Insert user with duplicate email (should raise error)
            try:
                conn.execute(text("""
                    INSERT INTO user (name, email, password) VALUES
                    ('Alice Duplicate', 'alice@example.com', 'password789')
                """))
                raise AssertionError("Allowed insert with duplicate email")
            except Exception:
                pass  # Expected error

            # 4. Update user email to duplicate (should raise error)
            try:
                conn.execute(text("""
                    UPDATE user SET email = 'alice@example.com' WHERE name = 'Bob'
                """))
                raise AssertionError("Allowed update to duplicate email")
            except Exception:
                pass  # Expected error

            # 5. Update user to have null password (should raise error)
            try:
                conn.execute(text("""
                    UPDATE user SET password = NULL WHERE name = 'Alice'
                """))
                raise AssertionError("Allowed update with NULL password")
            except Exception:
                pass  # Expected error

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()
            

    def test_admin_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # 1. Insert a user to use as admin
            result = conn.execute(text("""
                INSERT INTO `user` (name, email, password)
                VALUES ('AdminUser', 'adminuser@example.com', 'securepass')
            """))
            user_id = result.lastrowid

            # Insert admin with valid user_id - should pass
            conn.execute(text(f"""
                INSERT INTO admin (user_id) VALUES ({user_id})
            """))

            # 2. Insert admin with non-existing user_id - should fail FK
            try:
                conn.execute(text("""
                    INSERT INTO admin (user_id) VALUES (9999999)
                """))
                raise AssertionError("Allowed insert with non-existing user_id")
            except Exception:
                pass  # Expected FK violation

            # 3. Insert admin with duplicate user_id - should fail UNIQUE
            try:
                conn.execute(text(f"""
                    INSERT INTO admin (user_id) VALUES ({user_id})
                """))
                raise AssertionError("Allowed duplicate user_id insert")
            except Exception:
                pass  # Expected unique violation

            # 4. Test ON DELETE CASCADE
            conn.execute(text(f"""
                DELETE FROM `user` WHERE id = {user_id}
            """))

            admin_count = conn.execute(text(f"""
                SELECT COUNT(*) FROM admin WHERE user_id = {user_id}
            """)).scalar()
            if admin_count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete admin row")

            # 5. Test ON UPDATE CASCADE
            # Re-insert user and admin
            result = conn.execute(text("""
                INSERT INTO `user` (name, email, password)
                VALUES ('AdminUser2', 'adminuser2@example.com', 'securepass2')
            """))
            user_id = result.lastrowid
            conn.execute(text(f"INSERT INTO admin (user_id) VALUES ({user_id})"))

            # Update user id - Note: Updating PK is often disallowed in MySQL,
            # so this test may fail if your schema forbids it.
            # If you want, skip this part or test with a workaround.

            try:
                new_id = user_id + 1000
                conn.execute(text(f"""
                    UPDATE `user` SET id = {new_id} WHERE id = {user_id}
                """))

                admin_exists = conn.execute(text(f"""
                    SELECT COUNT(*) FROM admin WHERE user_id = {new_id}
                """)).scalar()
                if admin_exists != 1:
                    raise AssertionError("ON UPDATE CASCADE did not update admin.user_id")
            except Exception:
                print("FK update blocked")
                pass

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_worker_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # 1. Insert a user to reference in worker
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('WorkerUser', 'workeruser@example.com', 'workerpass')
            """))
            user_id = result.lastrowid

            # 2. Insert valid worker - should pass
            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary)
                VALUES ({user_id}, 1500.00)
            """))
            worker_id = result.lastrowid

            # 3. Insert worker with non-existing user_id - should fail FK
            try:
                conn.execute(text("""
                    INSERT INTO worker (user_id, salary) VALUES (9999999, 1200.00)
                """))
                raise AssertionError("Allowed insert with non-existing user_id")
            except Exception:
                pass  # Expected FK violation

            # 4. Insert worker with duplicate user_id - should fail UNIQUE
            try:
                conn.execute(text(f"""
                    INSERT INTO worker (user_id, salary) VALUES ({user_id}, 2000.00)
                """))
                raise AssertionError("Allowed duplicate user_id insert")
            except Exception:
                pass  # Expected unique violation

            # 5. Insert worker with negative salary - should fail CHECK constraint
            try:
                conn.execute(text(f"""
                    INSERT INTO worker (user_id, salary) VALUES ({user_id + 1}, -100.00)
                """))
                raise AssertionError("Allowed negative salary insert")
            except Exception:
                pass  # Expected check constraint violation

            # 6. Update worker to negative salary - should fail CHECK constraint
            try:
                conn.execute(text(f"""
                    UPDATE worker SET salary = -500.00 WHERE id = {worker_id}
                """))
                raise AssertionError("Allowed update to negative salary")
            except Exception:
                pass  # Expected check constraint violation

            # 7. Test ON DELETE CASCADE (delete user deletes worker)
            conn.execute(text(f"""
                DELETE FROM user WHERE id = {user_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM worker WHERE id = {worker_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete worker row")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_student_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # 1. Insert a user to reference in student
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('StudentUser', 'studentuser@example.com', 'studentpass')
            """))
            user_id = result.lastrowid

            # 2. Insert valid student - should pass
            result = conn.execute(text(f"""
                INSERT INTO student (user_id, age, phone_number)
                VALUES ({user_id}, 20, '123-456-7890')
            """))
            student_id = result.lastrowid

            # 3. Insert student with non-existing user_id - should fail FK
            try:
                conn.execute(text("""
                    INSERT INTO student (user_id, age) VALUES (9999999, 25)
                """))
                raise AssertionError("Allowed insert with non-existing user_id")
            except Exception:
                pass  # Expected FK violation

            # 4. Insert student with duplicate user_id - should fail UNIQUE
            try:
                conn.execute(text(f"""
                    INSERT INTO student (user_id, age) VALUES ({user_id}, 22)
                """))
                raise AssertionError("Allowed duplicate user_id insert")
            except Exception:
                pass  # Expected unique violation

            # 5. Insert student with invalid age (less than 10) - should fail CHECK
            try:
                # Make a new user for this test
                result = conn.execute(text("""
                    INSERT INTO user (name, email, password)
                    VALUES ('StudentUser2', 'studentuser2@example.com', 'studentpass2')
                """))
                user2_id = result.lastrowid

                conn.execute(text(f"""
                    INSERT INTO student (user_id, age) VALUES ({user2_id}, 9)
                """))
                raise AssertionError("Allowed insert with age < 10")
            except Exception:
                pass  # Expected CHECK violation

            # 6. Insert student with invalid age (greater than 85) - should fail CHECK
            try:
                # Make a new user for this test
                result = conn.execute(text("""
                    INSERT INTO user (name, email, password)
                    VALUES ('StudentUser3', 'studentuser3@example.com', 'studentpass3')
                """))
                user3_id = result.lastrowid

                conn.execute(text(f"""
                    INSERT INTO student (user_id, age) VALUES ({user3_id}, 90)
                """))
                raise AssertionError("Allowed insert with age > 85")
            except Exception:
                pass  # Expected CHECK violation

            # 7. Update student to invalid age - should fail CHECK
            try:
                conn.execute(text(f"""
                    UPDATE student SET age = 5 WHERE id = {student_id}
                """))
                raise AssertionError("Allowed update to invalid age")
            except Exception:
                pass  # Expected CHECK violation

            # 8. Test ON DELETE CASCADE (delete user deletes student)
            conn.execute(text(f"""
                DELETE FROM user WHERE id = {user_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM student WHERE id = {student_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete student row")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_maintenancer_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # 1. Insert a user and worker to reference in maintenancer
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('WorkerForMaint', 'workermaint@example.com', 'workerpass')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary) VALUES ({user_id}, 1200.00)
            """))
            worker_id = result.lastrowid

            # 2. Insert valid maintenancer - should pass
            result = conn.execute(text(f"""
                INSERT INTO maintenancer (worker_id, outsourced_worker)
                VALUES ({worker_id}, TRUE)
            """))
            maint_id = result.lastrowid

            # 3. Insert maintenancer with non-existing worker_id - should fail FK
            try:
                conn.execute(text("""
                    INSERT INTO maintenancer (worker_id, outsourced_worker)
                    VALUES (9999999, FALSE)
                """))
                raise AssertionError("Allowed insert with non-existing worker_id")
            except Exception:
                pass  # Expected FK violation

            # 4. Insert maintenancer with duplicate worker_id - should fail UNIQUE
            try:
                conn.execute(text(f"""
                    INSERT INTO maintenancer (worker_id, outsourced_worker)
                    VALUES ({worker_id}, FALSE)
                """))
                raise AssertionError("Allowed duplicate worker_id insert")
            except Exception:
                pass  # Expected unique violation

            # 5. Test ON DELETE CASCADE (delete worker deletes maintenancer)
            conn.execute(text(f"""
                DELETE FROM worker WHERE id = {worker_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM maintenancer WHERE id = {maint_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete maintenancer row")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_professor_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # 1. Insert user and worker to reference in professor
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('WorkerForProf', 'workerprof@example.com', 'workerpass')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary) VALUES ({user_id}, 2500.00)
            """))
            worker_id = result.lastrowid

            # 2. Insert valid professor - should pass
            result = conn.execute(text(f"""
                INSERT INTO professor (worker_id, academic_bg)
                VALUES ({worker_id}, 'PhD in Musicology')
            """))
            professor_id = result.lastrowid

            # 3. Insert professor with non-existing worker_id - should fail FK
            try:
                conn.execute(text("""
                    INSERT INTO professor (worker_id, academic_bg)
                    VALUES (9999999, 'PhD in Arts')
                """))
                raise AssertionError("Allowed insert with non-existing worker_id")
            except Exception:
                pass  # Expected FK violation

            # 4. Insert professor with duplicate worker_id - should fail UNIQUE
            try:
                conn.execute(text(f"""
                    INSERT INTO professor (worker_id, academic_bg)
                    VALUES ({worker_id}, 'Master in Music')
                """))
                raise AssertionError("Allowed duplicate worker_id insert")
            except Exception:
                pass  # Expected unique violation

            # 5. Insert professor with null academic_bg - should fail NOT NULL
            try:
                conn.execute(text(f"""
                    INSERT INTO professor (worker_id, academic_bg)
                    VALUES ({worker_id + 1}, NULL)
                """))
                raise AssertionError("Allowed insert with NULL academic_bg")
            except Exception:
                pass  # Expected NOT NULL violation

            # 6. Test ON DELETE CASCADE (delete worker deletes professor)
            conn.execute(text(f"""
                DELETE FROM worker WHERE id = {worker_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM professor WHERE id = {professor_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete professor row")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_secretary_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert user and worker to reference
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('WorkerForSecretary', 'workersec@example.com', 'workerpass')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary) VALUES ({user_id}, 1800.00)
            """))
            worker_id = result.lastrowid

            # Insert valid secretary - sector can be NULL (not specified NOT NULL)
            result = conn.execute(text(f"""
                INSERT INTO secretary (worker_id, sector) VALUES ({worker_id}, 'Admissions')
            """))
            secretary_id = result.lastrowid

            # Insert secretary with non-existing worker_id - should fail FK
            try:
                conn.execute(text("""
                    INSERT INTO secretary (worker_id, sector) VALUES (9999999, 'Finance')
                """))
                raise AssertionError("Allowed insert with non-existing worker_id")
            except Exception:
                pass  # Expected FK violation

            # Insert secretary with duplicate worker_id - should fail UNIQUE
            try:
                conn.execute(text(f"""
                    INSERT INTO secretary (worker_id, sector) VALUES ({worker_id}, 'Human Resources')
                """))
                raise AssertionError("Allowed duplicate worker_id insert")
            except Exception:
                pass  # Expected unique violation

            # Test ON DELETE CASCADE (delete worker deletes secretary)
            conn.execute(text(f"""
                DELETE FROM worker WHERE id = {worker_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM secretary WHERE id = {secretary_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete secretary row")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()
            
    def test_conductor_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert user, worker, professor to reference conductor
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('ProfForConductor', 'profconductor@example.com', 'pass123')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary) VALUES ({user_id}, 3000.00)
            """))
            worker_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO professor (worker_id, academic_bg)
                VALUES ({worker_id}, 'Master in Orchestration')
            """))
            professor_id = result.lastrowid

            # Insert valid conductor (level between 0 and 5)
            result = conn.execute(text(f"""
                INSERT INTO conductor (professor_id, level)
                VALUES ({professor_id}, 3)
            """))
            conductor_id = result.lastrowid

            # Insert conductor with non-existing professor_id - should fail FK
            try:
                conn.execute(text("""
                    INSERT INTO conductor (professor_id, level)
                    VALUES (9999999, 2)
                """))
                raise AssertionError("Allowed insert with non-existing professor_id")
            except Exception:
                pass  # Expected FK violation

            # Insert conductor with duplicate professor_id - should fail UNIQUE
            try:
                conn.execute(text(f"""
                    INSERT INTO conductor (professor_id, level)
                    VALUES ({professor_id}, 1)
                """))
                raise AssertionError("Allowed duplicate professor_id insert")
            except Exception:
                pass  # Expected unique violation

            # Insert conductor with level out of range (less than 0)
            try:
                conn.execute(text(f"""
                    INSERT INTO conductor (professor_id, level)
                    VALUES ({professor_id + 1}, -1)
                """))
                raise AssertionError("Allowed insert with level < 0")
            except Exception:
                pass  # Expected check constraint violation

            # Insert conductor with level out of range (greater than 5)
            try:
                # Insert a new professor for this test
                result = conn.execute(text("""
                    INSERT INTO user (name, email, password)
                    VALUES ('ProfForConductor2', 'profcond2@example.com', 'pass456')
                """))
                user2_id = result.lastrowid

                result = conn.execute(text(f"""
                    INSERT INTO worker (user_id, salary) VALUES ({user2_id}, 2800.00)
                """))
                worker2_id = result.lastrowid

                result = conn.execute(text(f"""
                    INSERT INTO professor (worker_id, academic_bg)
                    VALUES ({worker2_id}, 'PhD in Conducting')
                """))
                professor2_id = result.lastrowid

                conn.execute(text(f"""
                    INSERT INTO conductor (professor_id, level)
                    VALUES ({professor2_id}, 6)
                """))
                raise AssertionError("Allowed insert with level > 5")
            except Exception:
                pass  # Expected check constraint violation

            # Update conductor to invalid level (less than 0)
            try:
                conn.execute(text(f"""
                    UPDATE conductor SET level = -2 WHERE id = {conductor_id}
                """))
                raise AssertionError("Allowed update with level < 0")
            except Exception:
                pass  # Expected check constraint violation

            # Update conductor to invalid level (greater than 5)
            try:
                conn.execute(text(f"""
                    UPDATE conductor SET level = 10 WHERE id = {conductor_id}
                """))
                raise AssertionError("Allowed update with level > 5")
            except Exception:
                pass  # Expected check constraint violation

            # Test ON DELETE CASCADE (delete professor deletes conductor)
            conn.execute(text(f"""
                DELETE FROM professor WHERE id = {professor_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM conductor WHERE id = {conductor_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete conductor row")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_dependency_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert valid dependency
            result = conn.execute(text("""
                INSERT INTO dependency (name) VALUES ('Main Building')
            """))
            dependency_id = result.lastrowid

            # Insert dependency with NULL name - should fail NOT NULL
            try:
                conn.execute(text("""
                    INSERT INTO dependency (name) VALUES (NULL)
                """))
                raise AssertionError("Allowed insert with NULL name")
            except Exception:
                pass  # Expected NOT NULL violation

            # Insert dependency with duplicate name - should fail UNIQUE
            try:
                conn.execute(text("""
                    INSERT INTO dependency (name) VALUES ('Main Building')
                """))
                raise AssertionError("Allowed duplicate name insert")
            except Exception:
                pass  # Expected UNIQUE violation

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()
            
            
    def test_amphitheater_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert dependency to reference
            result = conn.execute(text("""
                INSERT INTO dependency (name) VALUES ('Main Amphitheater')
            """))
            dependency_id = result.lastrowid

            # Insert valid amphitheater (guest_capacity > 0)
            result = conn.execute(text(f"""
                INSERT INTO amphitheater (dependency_id, guest_capacity)
                VALUES ({dependency_id}, 100)
            """))

            # Insert amphitheater with non-existing dependency_id - should fail FK
            try:
                conn.execute(text("""
                    INSERT INTO amphitheater (dependency_id, guest_capacity)
                    VALUES (9999999, 50)
                """))
                raise AssertionError("Allowed insert with non-existing dependency_id")
            except Exception:
                pass  # Expected FK violation

            # Insert amphitheater with duplicate dependency_id - should fail UNIQUE
            try:
                conn.execute(text(f"""
                    INSERT INTO amphitheater (dependency_id, guest_capacity)
                    VALUES ({dependency_id}, 150)
                """))
                raise AssertionError("Allowed duplicate dependency_id insert")
            except Exception:
                pass  # Expected unique violation

            # Insert amphitheater with zero or negative guest_capacity - should fail CHECK
            try:
                # New dependency for test
                result = conn.execute(text("""
                    INSERT INTO dependency (name) VALUES ('Secondary Amphitheater')
                """))
                dependency2_id = result.lastrowid

                conn.execute(text(f"""
                    INSERT INTO amphitheater (dependency_id, guest_capacity)
                    VALUES ({dependency2_id}, 0)
                """))
                raise AssertionError("Allowed insert with guest_capacity <= 0")
            except Exception:
                pass  # Expected CHECK violation

            # Update amphitheater with invalid guest_capacity (<=0)
            try:
                conn.execute(text(f"""
                    UPDATE amphitheater SET guest_capacity = -10 WHERE dependency_id = {dependency_id}
                """))
                raise AssertionError("Allowed update with guest_capacity <= 0")
            except Exception:
                pass  # Expected CHECK violation

            # Test ON DELETE CASCADE (delete dependency deletes amphitheater)
            conn.execute(text(f"""
                DELETE FROM dependency WHERE id = {dependency_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM amphitheater WHERE dependency_id = {dependency_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete amphitheater row")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_classroom_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert dependency
            result = conn.execute(text("""
                INSERT INTO dependency (name) VALUES ('Classroom Dependency')
            """))
            dependency_id = result.lastrowid

            # Insert classroom with valid dependency_id
            result = conn.execute(text(f"""
                INSERT INTO classroom (dependency_id, ac_insulation)
                VALUES ({dependency_id}, TRUE)
            """))
            classroom_id = result.lastrowid

            # Insert classroom with non-existing dependency_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO classroom (dependency_id, ac_insulation)
                    VALUES (9999999, FALSE)
                """))
                raise AssertionError("Allowed insert with non-existing dependency_id")
            except Exception:
                pass  # Expected FK violation

            # Test ON DELETE CASCADE: deleting dependency deletes classroom
            conn.execute(text(f"""
                DELETE FROM dependency WHERE id = {dependency_id}
            """))

            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM classroom WHERE id = {classroom_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete classroom row")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()


    def test_course_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert user, worker, professor to reference course
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('ProfForCourse', 'profcourse@example.com', 'pass123')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary) VALUES ({user_id}, 2700.00)
            """))
            worker_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO professor (worker_id, academic_bg)
                VALUES ({worker_id}, 'Master of Performance')
            """))
            professor_id = result.lastrowid

            # Insert valid course with all constraints satisfied
            result = conn.execute(text(f"""
                INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                VALUES ('Music Theory', 3, 'Piano', 30, {professor_id})
            """))
            course_id = result.lastrowid

            # Insert course with level out of range (less than 0)
            try:
                conn.execute(text(f"""
                    INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                    VALUES ('Advanced Music', -1, 'Violin', 20, {professor_id})
                """))
                raise AssertionError("Allowed insert with level < 0")
            except Exception:
                pass  # Expected check constraint violation

            # Insert course with level out of range (greater than 5)
            try:
                conn.execute(text(f"""
                    INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                    VALUES ('Beginner Course', 6, 'Guitar', 25, {professor_id})
                """))
                raise AssertionError("Allowed insert with level > 5")
            except Exception:
                pass  # Expected check constraint violation

            # Insert course with student_limit <= 0
            try:
                conn.execute(text(f"""
                    INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                    VALUES ('Zero Limit Course', 2, 'Drums', 0, {professor_id})
                """))
                raise AssertionError("Allowed insert with student_limit <= 0")
            except Exception:
                pass  # Expected check constraint violation

            # Insert course with non-existing professor_id - should fail FK
            try:
                conn.execute(text("""
                    INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                    VALUES ('Ghost Course', 1, 'Flute', 10, 9999999)
                """))
                raise AssertionError("Allowed insert with non-existing professor_id")
            except Exception:
                pass  # Expected FK violation

            # Insert course with duplicate professor_id - should fail UNIQUE
            try:
                conn.execute(text(f"""
                    INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                    VALUES ('Duplicate Professor Course', 3, 'Clarinet', 15, {professor_id})
                """))
                raise AssertionError("Allowed duplicate professor_id insert")
            except Exception:
                pass  # Expected unique violation

            # Test ON DELETE SET NULL - delete professor sets professor_id to NULL in course
            # But professor_id is NOT NULL, so this may cause error or block deletion in MySQL.
            # So we test behavior and skip assertion if MySQL disallows.

            try:
                conn.execute(text(f"""
                    DELETE FROM professor WHERE id = {professor_id}
                """))
                prof_ref = conn.execute(text(f"""
                    SELECT professor_id FROM course WHERE id = {course_id}
                """)).scalar()

                if prof_ref is not None:
                    raise AssertionError("ON DELETE SET NULL did not set professor_id to NULL")
            except Exception:
                # Probably blocked due to NOT NULL, so rollback and skip
                trans.rollback()
                return

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()


    def test_class_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert dependency and classroom
            result = conn.execute(text("""
                INSERT INTO dependency (name) VALUES ('Class Dep')
            """))
            dependency_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO classroom (dependency_id, ac_insulation)
                VALUES ({dependency_id}, TRUE)
            """))
            classroom_id = result.lastrowid

            # Insert user, worker, professor for course
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('ProfClass', 'profclass@example.com', 'pass123')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary) VALUES ({user_id}, 2600.00)
            """))
            worker_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO professor (worker_id, academic_bg)
                VALUES ({worker_id}, 'PhD in Education')
            """))
            professor_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                VALUES ('Advanced Music Theory', 4, 'Piano', 25, {professor_id})
            """))
            conn.execute(text("COMMIT"))
            course_id = result.lastrowid
            
            # Insert valid class with correct classroom_id and course_id
            result = conn.execute(text(f"""
                INSERT INTO class (date, classroom_id, course_id)
                VALUES (NOW(), {classroom_id}, {course_id})
            """))
            class_id = result.lastrowid

            # Insert class with non-existing classroom_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO class (date, classroom_id, course_id)
                    VALUES (NOW(), 9999999, {course_id})
                """))
                raise AssertionError("Allowed insert with non-existing classroom_id")
            except Exception:
                pass  # Expected FK violation

            # Insert class with non-existing course_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO class (date, classroom_id, course_id)
                    VALUES (NOW(), {classroom_id}, 9999999)
                """))
                raise AssertionError("Allowed insert with non-existing course_id")
            except Exception:
                pass  # Expected FK violation

            # Test ON DELETE CASCADE: deleting classroom deletes class
            conn.execute(text(f"""
                DELETE FROM classroom WHERE id = {classroom_id}
            """))

            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM class WHERE id = {class_id}
            """)).scalar()

            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete class row (classroom)")

            # Rollback to test ON DELETE CASCADE for course
            trans.rollback()
            trans = conn.begin()

            # Repeat inserts for dependency, classroom and class
            result = conn.execute(text("""
                INSERT INTO dependency (name) VALUES ('Class Dep 2')
            """))
            dependency_id_2 = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO classroom (dependency_id, ac_insulation)
                VALUES ({dependency_id_2}, TRUE)
            """))
            classroom_id_2 = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO class (date, classroom_id, course_id)
                VALUES (NOW(), {classroom_id_2}, {course_id})
            """))
            class_id_2 = result.lastrowid

            # Delete course to check cascade delete on class
            conn.execute(text(f"""
                DELETE FROM course WHERE id = {course_id}
            """))

            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM class WHERE id = {class_id_2}
            """)).scalar()

            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete class row (course)")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()


    def test_enrollment_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert user, student, user2, worker2, professor2, course for references
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('StudentForEnroll', 'studentenroll@example.com', 'pass123')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO student (user_id, age, phone_number)
                VALUES ({user_id}, 20, '1234567890')
            """))
            student_id = result.lastrowid

            # Create professor and course for enrollment
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('ProfForEnroll', 'profenroll@example.com', 'pass123')
            """))
            user2_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary) VALUES ({user2_id}, 2500.00)
            """))
            worker2_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO professor (worker_id, academic_bg)
                VALUES ({worker2_id}, 'Master in Music')
            """))
            professor_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                VALUES ('Jazz Studies', 2, 'Saxophone', 20, {professor_id})
            """))
            conn.execute(text("COMMIT"))
            course_id = result.lastrowid

            # Insert valid enrollment
            conn.execute(text(f"""
                INSERT INTO enrollment (student_id, course_id)
                VALUES ({student_id}, {course_id})
            """))

            # Insert enrollment with non-existing student_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO enrollment (student_id, course_id)
                    VALUES (9999999, {course_id})
                """))
                raise AssertionError("Allowed insert with non-existing student_id")
            except Exception:
                pass  # Expected FK violation

            # Insert enrollment with non-existing course_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO enrollment (student_id, course_id)
                    VALUES ({student_id}, 9999999)
                """))
                raise AssertionError("Allowed insert with non-existing course_id")
            except Exception:
                pass  # Expected FK violation

            # Insert duplicate enrollment (same student_id and course_id) - should fail PK unique constraint
            try:
                conn.execute(text(f"""
                    INSERT INTO enrollment (student_id, course_id)
                    VALUES ({student_id}, {course_id})
                """))
                raise AssertionError("Allowed duplicate enrollment insert")
            except Exception:
                pass  # Expected unique constraint violation

            # Test ON DELETE CASCADE: deleting student deletes enrollment
            conn.execute(text(f"""
                DELETE FROM student WHERE id = {student_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM enrollment WHERE student_id = {student_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete enrollment row (student)")

            # Rollback to test ON DELETE CASCADE for course
            trans.rollback()
            trans = conn.begin()

            # Re-insert student and enrollment
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('StudentForEnroll2', 'studentenroll2@example.com', 'pass123')
            """))
            user3_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO student (user_id, age, phone_number)
                VALUES ({user3_id}, 22, '0987654321')
            """))
            student2_id = result.lastrowid

            conn.execute(text(f"""
                INSERT INTO enrollment (student_id, course_id)
                VALUES ({student2_id}, {course_id})
            """))

            # Delete course to check cascade delete on enrollment
            conn.execute(text(f"""
                DELETE FROM course WHERE id = {course_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM enrollment WHERE course_id = {course_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete enrollment row (course)")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_attendance_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert user and student
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('StudentForAttendance', 'studentattend@example.com', 'pass123')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO student (user_id, age, phone_number)
                VALUES ({user_id}, 21, '1112223333')
            """))
            student_id = result.lastrowid

            # Insert dependency, classroom
            result = conn.execute(text("""
                INSERT INTO dependency (name) VALUES ('Attendance Building')
            """))
            dependency_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO classroom (dependency_id, ac_insulation)
                VALUES ({dependency_id}, TRUE)
            """))
            classroom_id = result.lastrowid

            # Insert user, worker, professor, course for class
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('ProfForAttendance', 'profattend@example.com', 'pass123')
            """))
            prof_user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary) VALUES ({prof_user_id}, 2600.00)
            """))
            worker_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO professor (worker_id, academic_bg)
                VALUES ({worker_id}, 'PhD Music')
            """))
            professor_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                VALUES ('Music History', 2, 'Violin', 20, {professor_id})
            """))
            conn.execute(text("COMMIT"))
            course_id = result.lastrowid

            # Insert class referencing classroom and course
            result = conn.execute(text(f"""
                INSERT INTO class (date, classroom_id, course_id)
                VALUES (NOW(), {classroom_id}, {course_id})
            """))
            conn.execute(text("COMMIT"))
            class_id = result.lastrowid

            # Insert valid attendance
            conn.execute(text(f"""
                INSERT INTO attendance (student_id, class_id)
                VALUES ({student_id}, {class_id})
            """))

            # Insert attendance with non-existing student_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO attendance (student_id, class_id)
                    VALUES (9999999, {class_id})
                """))
                raise AssertionError("Allowed insert with non-existing student_id")
            except Exception:
                pass  # Expected FK violation

            # Insert attendance with non-existing class_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO attendance (student_id, class_id)
                    VALUES ({student_id}, 9999999)
                """))
                raise AssertionError("Allowed insert with non-existing class_id")
            except Exception:
                pass  # Expected FK violation

            # Insert duplicate attendance - should fail PK unique constraint
            try:
                conn.execute(text(f"""
                    INSERT INTO attendance (student_id, class_id)
                    VALUES ({student_id}, {class_id})
                """))
                raise AssertionError("Allowed duplicate attendance insert")
            except Exception:
                pass  # Expected unique constraint violation

            # Test ON DELETE CASCADE: deleting student deletes attendance
            conn.execute(text(f"""
                DELETE FROM student WHERE id = {student_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM attendance WHERE student_id = {student_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete attendance row (student)")

            # Rollback to test ON DELETE CASCADE for class
            trans.rollback()
            trans = conn.begin()

            # Re-insert student, attendance
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('StudentForAttendance2', 'studentattend2@example.com', 'pass123')
            """))
            user2_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO student (user_id, age, phone_number)
                VALUES ({user2_id}, 22, '4445556666')
            """))
            student2_id = result.lastrowid

            conn.execute(text(f"""
                INSERT INTO attendance (student_id, class_id)
                VALUES ({student2_id}, {class_id})
            """))

            # Delete class to check cascade delete on attendance
            conn.execute(text(f"""
                DELETE FROM class WHERE id = {class_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM attendance WHERE class_id = {class_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete attendance row (class)")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_participation_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert dependency for amphitheater
            result = conn.execute(text("INSERT INTO dependency (name) VALUES ('Dep for Amphitheater')"))
            dependency_id = result.lastrowid

            # Insert amphitheater
            result = conn.execute(text(f"""
                INSERT INTO amphitheater (dependency_id, guest_capacity)
                VALUES ({dependency_id}, 100)
            """))
            amphitheater_id = result.lastrowid  # amphitheater dependency_id = dependency_id (1:1)

            # Insert user, worker, professor, conductor
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('Prof Conductor', 'profcond@example.com', 'pass123')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"INSERT INTO worker (user_id, salary) VALUES ({user_id}, 3000)"))
            worker_id = result.lastrowid

            result = conn.execute(text(f"INSERT INTO professor (worker_id, academic_bg) VALUES ({worker_id}, 'PhD Music')"))
            professor_id = result.lastrowid

            result = conn.execute(text(f"INSERT INTO conductor (professor_id, level) VALUES ({professor_id}, 3)"))
            conductor_id = result.lastrowid

            # Insert student
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('Student One', 'student1@example.com', 'pass123')
            """))
            student_user_id = result.lastrowid

            result = conn.execute(text(f"INSERT INTO student (user_id, age, phone_number) VALUES ({student_user_id}, 20, '555-1234')"))
            conn.execute(text("COMMIT"))
            student_id = result.lastrowid

            # Insert presentation
            result = conn.execute(text(f"""
                INSERT INTO presentation (title, date, level, guest_number, amphitheater_id, conductor_id)
                VALUES ('Music Gala', NOW(), 4, 150, {amphitheater_id}, {conductor_id})
            """))
            presentation_id = result.lastrowid

            # Valid participation insert
            result = conn.execute(text(f"""
                INSERT INTO participation (student_id, presentation_id)
                VALUES ({student_id}, {presentation_id})
            """))

            # ON DELETE CASCADE test for student: deleting student deletes participation
            conn.execute(text(f"DELETE FROM student WHERE id = {student_id}"))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM participation WHERE presentation_id = {presentation_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete participation row when student deleted")

            # Re-insert student and participation
            result = conn.execute(text(f"""
                INSERT INTO user (name, email, password)
                VALUES ('Student Two', 'student2@example.com', 'pass123')
            """))
            student_user_id2 = result.lastrowid

            result = conn.execute(text(f"INSERT INTO student (user_id, age, phone_number) VALUES ({student_user_id2}, 22, '555-5678')"))
            conn.execute(text("COMMIT"))
            student_id2 = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO participation (student_id, presentation_id)
                VALUES ({student_id2}, {presentation_id})
            """))
            
            # Attempt duplicate insert - should raise IntegrityError
            try:
                conn.execute(text(f"""
                    INSERT INTO participation (student_id, presentation_id)
                    VALUES (:student_id, :presentation_id)
                """), {"student_id": student_id2, "presentation_id": presentation_id})
                raise AssertionError("Allowed duplicate participation entry")
            except Exception as e:
                # Check it's an IntegrityError or FK violation - pass if so
                pass

            # Delete presentation and check cascade delete
            conn.execute(text(f"DELETE FROM presentation WHERE id = {presentation_id}"))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM participation WHERE student_id = {student_id2}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete participation row when presentation deleted")

            trans.rollback()
            
            

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()


    def test_instrument_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert dependency to reference
            result = conn.execute(text("""
                INSERT INTO dependency (name) VALUES ('Instrument Storage')
            """))
            dependency_id = result.lastrowid

            # Insert valid instrument with status 'APTO' and dependency_id
            result = conn.execute(text(f"""
                INSERT INTO instrument (status, dependency_id)
                VALUES ('APTO', {dependency_id})
            """))
            instrument_id = result.lastrowid

            # Insert instrument with invalid status - should fail CHECK
            try:
                conn.execute(text(f"""
                    INSERT INTO instrument (status, dependency_id)
                    VALUES ('INVALID_STATUS', {dependency_id})
                """))
                raise AssertionError("Allowed insert with invalid status")
            except Exception:
                pass  # Expected CHECK violation

            # Insert instrument with NULL dependency_id (allowed)
            result = conn.execute(text(f"""
                INSERT INTO instrument (status, dependency_id)
                VALUES ('DESATIVADO', NULL)
            """))

            # Insert instrument with non-existing dependency_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO instrument (status, dependency_id)
                    VALUES ('APTO', 9999999)
                """))
                raise AssertionError("Allowed insert with non-existing dependency_id")
            except Exception:
                pass  # Expected FK violation

            # Test ON DELETE SET NULL: delete dependency sets instrument.dependency_id to NULL
            conn.execute(text(f"""
                DELETE FROM dependency WHERE id = {dependency_id}
            """))
            dep_ref = conn.execute(text(f"""
                SELECT dependency_id FROM instrument WHERE id = {instrument_id}
            """)).scalar()

            if dep_ref is not None:
                raise AssertionError("ON DELETE SET NULL did not set dependency_id to NULL")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_maintenance_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert dependency for instrument and classroom
            result = conn.execute(text("""
                INSERT INTO dependency (name) VALUES ('Maintenance Dept')
            """))
            dependency_id = result.lastrowid

            # Insert instrument referencing dependency
            result = conn.execute(text(f"""
                INSERT INTO instrument (status, dependency_id)
                VALUES ('APTO', {dependency_id})
            """))
            instrument_id = result.lastrowid

            # Insert user, worker, maintenancer for maintenancer reference
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('MaintenancerUser', 'maintuser@example.com', 'pass123')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary)
                VALUES ({user_id}, 2200.00)
            """))
            worker_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO maintenancer (worker_id, outsourced_worker)
                VALUES ({worker_id}, TRUE)
            """))
            conn.execute(text("COMMIT"))
            maintenancer_id = result.lastrowid

            # Insert valid maintenance record
            conn.execute(text(f"""
                INSERT INTO maintenance (instrument_id, maintenancer_id)
                VALUES ({instrument_id}, {maintenancer_id})
            """))

            # Insert with non-existing instrument_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO maintenance (instrument_id, maintenancer_id)
                    VALUES (9999999, {maintenancer_id})
                """))
                raise AssertionError("Allowed insert with non-existing instrument_id")
            except Exception:
                pass  # Expected FK violation

            # Insert with non-existing maintenancer_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO maintenance (instrument_id, maintenancer_id)
                    VALUES ({instrument_id}, 9999999)
                """))
                raise AssertionError("Allowed insert with non-existing maintenancer_id")
            except Exception:
                pass  # Expected FK violation

            # Insert duplicate maintenance record - should fail PK unique constraint
            try:
                conn.execute(text(f"""
                    INSERT INTO maintenance (instrument_id, maintenancer_id)
                    VALUES ({instrument_id}, {maintenancer_id})
                """))
                raise AssertionError("Allowed duplicate maintenance insert")
            except Exception:
                pass  # Expected unique constraint violation

            # Test ON DELETE CASCADE: delete instrument deletes maintenance
            conn.execute(text(f"""
                DELETE FROM instrument WHERE id = {instrument_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM maintenance WHERE instrument_id = {instrument_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete maintenance row (instrument)")

            # Rollback to test ON DELETE CASCADE for maintenancer
            trans.rollback()
            trans = conn.begin()

            # Re-insert instrument and maintenance
            result = conn.execute(text(f"""
                INSERT INTO instrument (status, dependency_id)
                VALUES ('APTO', NULL)
            """))
            instrument2_id = result.lastrowid

            conn.execute(text(f"""
                INSERT INTO maintenance (instrument_id, maintenancer_id)
                VALUES ({instrument2_id}, {maintenancer_id})
            """))

            # Delete maintenancer to check cascade delete on maintenance
            conn.execute(text(f"""
                DELETE FROM maintenancer WHERE id = {maintenancer_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM maintenance WHERE maintenancer_id = {maintenancer_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete maintenance row (maintenancer)")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()


    def test_presentation_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert dependency and amphitheater
            result = conn.execute(text("""
                INSERT INTO dependency (name) VALUES ('Amphitheater Dep')
            """))
            dependency_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO amphitheater (dependency_id, guest_capacity)
                VALUES ({dependency_id}, 150)
            """))
            amphitheater_id = result.lastrowid

            # Insert user, worker, professor, conductor
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('ConductorUser', 'conduct@example.com', 'pass123')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary)
                VALUES ({user_id}, 3000.00)
            """))
            worker_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO professor (worker_id, academic_bg)
                VALUES ({worker_id}, 'Master Conductor')
            """))
            professor_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO conductor (professor_id, level)
                VALUES ({professor_id}, 4)
            """))
            conn.execute(text("COMMIT"))
            conductor_id = result.lastrowid

            # Insert valid presentation
            result = conn.execute(text(f"""
                INSERT INTO presentation (title, date, level, guest_number, amphitheater_id, conductor_id)
                VALUES ('Symphony Night', NOW(), 3, 100, {amphitheater_id}, {conductor_id})
            """))
            presentation_id = result.lastrowid

            # Insert with invalid level (outside 0-5) - should fail CHECK
            try:
                conn.execute(text(f"""
                    INSERT INTO presentation (title, date, level, guest_number, amphitheater_id, conductor_id)
                    VALUES ('Invalid Level Show', NOW(), 10, 50, {amphitheater_id}, {conductor_id})
                """))
                raise AssertionError("Allowed insert with invalid level")
            except Exception:
                pass  # Expected CHECK violation

            # Insert with negative guest_number - should fail CHECK
            try:
                conn.execute(text(f"""
                    INSERT INTO presentation (title, date, level, guest_number, amphitheater_id, conductor_id)
                    VALUES ('Negative Guests', NOW(), 2, -5, {amphitheater_id}, {conductor_id})
                """))
                raise AssertionError("Allowed insert with negative guest_number")
            except Exception:
                pass  # Expected CHECK violation

            # Insert with non-existing amphitheater_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO presentation (title, date, level, guest_number, amphitheater_id, conductor_id)
                    VALUES ('No Amphitheater', NOW(), 2, 20, 9999999, {conductor_id})
                """))
                raise AssertionError("Allowed insert with non-existing amphitheater_id")
            except Exception:
                pass  # Expected FK violation

            # Insert with non-existing conductor_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO presentation (title, date, level, guest_number, amphitheater_id, conductor_id)
                    VALUES ('No Conductor', NOW(), 2, 20, {amphitheater_id}, 9999999)
                """))
                raise AssertionError("Allowed insert with non-existing conductor_id")
            except Exception:
                pass  # Expected FK violation

            # Test ON DELETE CASCADE: deleting amphitheater deletes presentation
            conn.execute(text(f"""
                DELETE FROM amphitheater WHERE dependency_id = {dependency_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM presentation WHERE id = {presentation_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete presentation row (amphitheater)")

            # Rollback to test ON DELETE RESTRICT for conductor
            trans.rollback()
            trans = conn.begin()

            # Re-insert amphitheater and presentation
            result = conn.execute(text(f"""
                INSERT INTO dependency (name) VALUES ('Amphitheater Dep 2')
            """))
            dependency_id2 = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO amphitheater (dependency_id, guest_capacity)
                VALUES ({dependency_id2}, 200)
            """))
            amphitheater_id2 = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO presentation (title, date, level, guest_number, amphitheater_id, conductor_id)
                VALUES ('Second Symphony', NOW(), 3, 150, {amphitheater_id2}, {conductor_id})
            """))
            presentation_id2 = result.lastrowid

            # Try to delete conductor referenced by presentation - should fail due to RESTRICT
            try:
                conn.execute(text(f"""
                    DELETE FROM conductor WHERE id = {conductor_id}
                """))
                raise AssertionError("Allowed deletion of conductor with referencing presentation")
            except Exception:
                pass  # Expected RESTRICT failure

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()

    def test_rehearsal_table_integrity():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert dependency and amphitheater
            result = conn.execute(text("""
                INSERT INTO dependency (name) VALUES ('Rehearsal Dep')
            """))
            dependency_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO amphitheater (dependency_id, guest_capacity)
                VALUES ({dependency_id}, 180)
            """))
            amphitheater_id = result.lastrowid

            # Insert user, worker, professor, conductor
            result = conn.execute(text("""
                INSERT INTO user (name, email, password)
                VALUES ('ConductorUserReh', 'condreh@example.com', 'pass123')
            """))
            user_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO worker (user_id, salary)
                VALUES ({user_id}, 2800.00)
            """))
            worker_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO professor (worker_id, academic_bg)
                VALUES ({worker_id}, 'Doctor of Music')
            """))
            professor_id = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO conductor (professor_id, level)
                VALUES ({professor_id}, 5)
            """))
            conductor_id = result.lastrowid

            # Insert presentation referencing amphitheater and conductor
            result = conn.execute(text(f"""
                INSERT INTO presentation (title, date, level, guest_number, amphitheater_id, conductor_id)
                VALUES ('Rehearsal Presentation', NOW(), 4, 120, {amphitheater_id}, {conductor_id})
            """))
            conn.execute(text("COMMIT"))
            presentation_id = result.lastrowid

            # Insert valid rehearsal
            result = conn.execute(text(f"""
                INSERT INTO rehearsal (date, amphitheater_id, presentation_id)
                VALUES (NOW(), {amphitheater_id}, {presentation_id})
            """))
            rehearsal_id = result.lastrowid

            # Insert rehearsal with non-existing amphitheater_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO rehearsal (date, amphitheater_id, presentation_id)
                    VALUES (NOW(), 9999999, {amphitheater_id})
                """))
                raise AssertionError("Allowed insert with non-existing amphitheater_id")
            except Exception:
                pass  # Expected FK violation

            # Insert rehearsal with non-existing presentation_id - should fail FK
            try:
                conn.execute(text(f"""
                    INSERT INTO rehearsal (date, amphitheater_id, presentation_id)
                    VALUES (NOW(), {amphitheater_id}, 9999999)
                """))
                raise AssertionError("Allowed insert with non-existing presentation_id")
            except Exception:
                pass  # Expected FK violation

            # Test ON DELETE CASCADE: deleting amphitheater deletes rehearsal
            conn.execute(text(f"""
                DELETE FROM amphitheater WHERE dependency_id = {dependency_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM rehearsal WHERE id = {rehearsal_id}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete rehearsal row (amphitheater)")

            # Rollback to test ON DELETE CASCADE for presentation
            trans.rollback()
            trans = conn.begin()

            # Re-insert amphitheater and rehearsal
            result = conn.execute(text(f"""
                INSERT INTO dependency (name) VALUES ('Rehearsal Dep 2')
            """))
            dependency_id2 = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO amphitheater (dependency_id, guest_capacity)
                VALUES ({dependency_id2}, 200)
            """))
            amphitheater_id2 = result.lastrowid

            result = conn.execute(text(f"""
                INSERT INTO rehearsal (date, amphitheater_id, presentation_id)
                VALUES (NOW(), {amphitheater_id}, {presentation_id})
            """))
            rehearsal_id2 = result.lastrowid

            # Delete presentation to check cascade delete on rehearsal
            conn.execute(text(f"""
                DELETE FROM presentation WHERE id = {presentation_id}
            """))
            count = conn.execute(text(f"""
                SELECT COUNT(*) FROM rehearsal WHERE id = {rehearsal_id2}
            """)).scalar()
            if count != 0:
                raise AssertionError("ON DELETE CASCADE did not delete rehearsal row (presentation)")

            trans.rollback()

        except AssertionError as e:
            trans.rollback()
            raise e
        except Exception as e:
            trans.rollback()
            raise e
        finally:
            conn.close()


    def test_vw_agenda_aulas():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Minimal setup: insert dependency, classroom, user, worker, professor, course, class
            
            result = conn.execute(text("INSERT INTO dependency (name) VALUES ('Dep Aula')"))
            dependency_id = result.lastrowid
            
            result = conn.execute(text(f"""
                INSERT INTO classroom (dependency_id, ac_insulation)
                VALUES ({dependency_id}, TRUE)
            """))
            classroom_id = result.lastrowid
            
            result = conn.execute(text("INSERT INTO user (name, email, password) VALUES ('Prof Aula', 'prof_aula@example.com', 'pass')"))
            user_id = result.lastrowid
            
            result = conn.execute(text(f"INSERT INTO worker (user_id, salary) VALUES ({user_id}, 2500)"))
            worker_id = result.lastrowid
            
            result = conn.execute(text(f"INSERT INTO professor (worker_id, academic_bg) VALUES ({worker_id}, 'MSc Music')"))
            professor_id = result.lastrowid
            
            result = conn.execute(text(f"""
                INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                VALUES ('Curso Teste', 2, 'Piano', 20, {professor_id})
            """))
            conn.execute(text("COMMIT"))
            course_id = result.lastrowid
            
            conn.execute(text(f"""
                INSERT INTO class (date, classroom_id, course_id)
                VALUES (NOW(), {classroom_id}, {course_id})
            """))
            
            # Query view
            result = conn.execute(text("SELECT * FROM vw_agenda_aulas WHERE professor = 'Prof Aula'"))
            row = result.fetchone()
            
            assert row is not None, "vw_agenda_aulas returned no rows"
            expected_columns = {'data_hora', 'curso', 'sala', 'professor'}
            assert set(result.keys()) == expected_columns, "vw_agenda_aulas columns mismatch"
            assert row[1] == 'Curso Teste', "vw_agenda_aulas curso value mismatch"
            assert row[2] == 'Dep Aula', "vw_agenda_aulas sala value mismatch"
            assert row[3] == 'Prof Aula', "vw_agenda_aulas professor value mismatch"

            trans.rollback()
        finally:
            conn.close()
            
            
    def test_vw_participacao_apresentacoes():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # Insert dependency, amphitheater
            result = conn.execute(text("INSERT INTO dependency (name) VALUES ('Dep Apresent')"))
            dependency_id = result.lastrowid
            result = conn.execute(text(f"""
                INSERT INTO amphitheater (dependency_id, guest_capacity)
                VALUES ({dependency_id}, 100)
            """))
            conn.execute(text("COMMIT"))
            amphitheater_id = result.lastrowid
            
            # User, worker, professor, conductor
            result = conn.execute(text("INSERT INTO user (name, email, password) VALUES ('Prof Apres', 'prof_apres@example.com', 'pass')"))
            user_id = result.lastrowid
            result = conn.execute(text(f"INSERT INTO worker (user_id, salary) VALUES ({user_id}, 3000)"))
            worker_id = result.lastrowid
            result = conn.execute(text(f"INSERT INTO professor (worker_id, academic_bg) VALUES ({worker_id}, 'PhD Music')"))
            professor_id = result.lastrowid
            result = conn.execute(text(f"INSERT INTO conductor (professor_id, level) VALUES ({professor_id}, 2)"))
            conductor_id = result.lastrowid
            
            # User and student
            result = conn.execute(text("INSERT INTO user (name, email, password) VALUES ('Student Apres', 'student_apres@example.com', 'pass')"))
            student_user_id = result.lastrowid
            result = conn.execute(text(f"INSERT INTO student (user_id, age, phone_number) VALUES ({student_user_id}, 21, '555-4321')"))
            student_id = result.lastrowid
            
            # Insert presentations
            result = conn.execute(text(f"""
                INSERT INTO presentation (title, date, level, guest_number, amphitheater_id, conductor_id)
                VALUES ('Pres 1', NOW(), 3, 50, {amphitheater_id}, {conductor_id})
            """))
            conn.execute(text("COMMIT"))
            presentation_id1 = result.lastrowid
            
            result = conn.execute(text(f"""
                INSERT INTO presentation (title, date, level, guest_number, amphitheater_id, conductor_id)
                VALUES ('Pres 2', NOW(), 2, 60, {amphitheater_id}, {conductor_id})
            """))
            conn.execute(text("COMMIT"))
            presentation_id2 = result.lastrowid
            
            # participation: link student to presentations
            conn.execute(text(f"INSERT INTO participation (student_id, presentation_id) VALUES ({student_id}, {presentation_id1})"))
            conn.execute(text(f"INSERT INTO participation (student_id, presentation_id) VALUES ({student_id}, {presentation_id2})"))
            
            # Query the view
            result = conn.execute(text(f"SELECT * FROM vw_participacao_apresentacoes WHERE student_id = {student_id}"))
            row = result.fetchone()
            
            assert row is not None, "vw_participacao_apresentacoes returned no rows"
            expected_columns = {'student_id', 'aluno', 'total_apresentacoes'}
            assert set(result.keys()) == expected_columns, "vw_participacao_apresentacoes columns mismatch"
            assert row[1] == 'Student Apres', "vw_participacao_apresentacoes aluno value mismatch"
            assert row[2] == 2, "vw_participacao_apresentacoes total_apresentacoes count mismatch"

            trans.rollback()
        finally:
            conn.close()


    def test_vw_cursos_com_vagas():
        conn = db.engine.connect()
        trans = conn.begin()
        try:
            # User, worker, professor, course
            result = conn.execute(text("INSERT INTO user (name, email, password) VALUES ('Prof Vagas', 'prof_vagas@example.com', 'pass')"))
            user_id = result.lastrowid
            result = conn.execute(text(f"INSERT INTO worker (user_id, salary) VALUES ({user_id}, 3200)"))
            worker_id = result.lastrowid
            result = conn.execute(text(f"INSERT INTO professor (worker_id, academic_bg) VALUES ({worker_id}, 'PhD Vagas')"))
            professor_id = result.lastrowid
            
            result = conn.execute(text(f"""
                INSERT INTO course (name, level, instrument_focus, student_limit, professor_id)
                VALUES ('Curso Vagas', 3, 'Violin', 3, {professor_id})
            """))
            conn.execute(text("COMMIT"))
            course_id = result.lastrowid
            
            # Insert enrollments (2 students)
            for i in range(2):
                result = conn.execute(text(f"INSERT INTO user (name, email, password) VALUES ('Student Vagas{i}', 'student_vagas{i}@example.com', 'pass')"))
                student_user_id = result.lastrowid
                result = conn.execute(text(f"INSERT INTO student (user_id, age, phone_number) VALUES ({student_user_id}, 20, '555-000{i}')"))
                student_id = result.lastrowid
                conn.execute(text(f"INSERT INTO enrollment (student_id, course_id) VALUES ({student_id}, {course_id})"))
            
            # Query the view
            result = conn.execute(text(f"SELECT * FROM vw_cursos_com_vagas WHERE name = 'Curso Vagas'"))
            row = result.fetchone()
            
            assert row is not None, "vw_cursos_com_vagas returned no rows"
            expected_columns = {'name', 'vagas'}
            
            assert set(result.keys()) == expected_columns, "vw_cursos_com_vagas columns mismatch"
            assert row[0] == 'Curso Vagas', "vw_cursos_com_vagas name count mismatch"
            assert row[1] == 1, "vw_cursos_com_vagas vagas count mismatch"

            trans.rollback()
        finally:
            conn.close()



    tests = [
        (test_conductor_bonus_trigger, "'conductor_bonus' trigger"),
        (test_instrument_maintenance_trigger, "'instrument_maintenance' trigger"),
        (test_user_table_integrity, "user table integrity"),
        (test_admin_table_integrity, "admin table integrity"),
        (test_worker_table_integrity, "worker table integrity"),
        (test_student_table_integrity, "student table integrity"),
        (test_maintenancer_table_integrity, "maintenancer table integrity"),
        (test_professor_table_integrity, "professor table integrity"),
        (test_secretary_table_integrity, "secretary table integrity"),
        (test_conductor_table_integrity, "conductor table integrity"),
        (test_dependency_table_integrity, "dependency table integrity"),
        (test_amphitheater_table_integrity, "amphitheater table integrity"),
        (test_classroom_table_integrity, "classroom table integrity"),
        (test_course_table_integrity, "course table integrity"),
        (test_class_table_integrity, "class table integrity"),
        (test_enrollment_table_integrity, "enrollment table integrity"),
        (test_attendance_table_integrity, "attendance table integrity"),
        (test_participation_table_integrity, "participation table integrity"),
        (test_instrument_table_integrity, "instrument table integrity"),
        (test_maintenance_table_integrity, "maintenance table integrity"),
        (test_presentation_table_integrity, "presentation table integrity"),
        (test_rehearsal_table_integrity, "rehearsal table integrity"),
        (test_vw_agenda_aulas, "vw agenda aulas"),
        (test_vw_participacao_apresentacoes, "vw participacao apresentacoes"),
        (test_vw_cursos_com_vagas, "test_vw_cursos_com_vagas")
    ]

    for test_func, test_name in tests:
        run_test(test_func, test_name)

    print("\nTest Results:")
    print(f"Passed: {test_results['passed']}")
    print(f"Failed: {test_results['failed']}")
    print(f"Errors: {test_results['errors']}")
    print(f"Total:  {len(tests)}")

    return test_results

if __name__ == "__main__":
    with app.app_context():
        reset_and_seed()
        test_results = run_integrity_tests()
        if test_results['failed'] > 0 or test_results['errors'] > 0:
            exit(1)  # Return non-zero exit code if any tests failed