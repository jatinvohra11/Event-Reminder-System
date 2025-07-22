public class Main {
    public static void main(String[] args) {
        ReminderManager manager = new ReminderManager();

        Event event1 = new Event("Doctor Appointment", "Visit Dr. Sharma", "2025-07-25", "10:00 AM");
        manager.addEvent(event1);

        for (Event e : manager.getEvents()) {
            System.out.println(e);
        }
    }
}
