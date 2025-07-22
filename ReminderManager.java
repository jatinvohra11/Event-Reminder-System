import java.util.ArrayList;
import java.util.List;

public class ReminderManager {
    private List<Event> events;

    public ReminderManager() {
        events = new ArrayList<>();
    }

    public void addEvent(Event e) {
        events.add(e);
    }

    public void deleteEvent(String title) {
        events.removeIf(event -> event.getTitle().equalsIgnoreCase(title));
    }

    public List<Event> getEvents() {
        return events;
    }
}
