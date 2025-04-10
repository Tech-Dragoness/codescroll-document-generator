#include <iostream>
using namespace std;

class Wizard {
public:
    string name;
    int level;

    Wizard(string n, int l) {
        name = n;
        level = l;
    }

    void castSpell() {
        cout << name << " casts a spell of level " << level << "!" << endl;
    }

    int getLevel() {
        return level;
    }
};

int main() {
    Wizard merlin("Merlin", 99);

    merlin.castSpell();

    if (merlin.getLevel() > 50) {
        cout << "A powerful wizard appears!" << endl;
    }

    for (int i = 0; i < 3; i++) {
        cout << "Magic surge #" << i << endl;
    }

    while (merlin.getLevel() > 0) {
        cout << "Power drains..." << endl;
        break;
    }

    try {
        throw runtime_error("Spell misfire!");
    } catch (exception& e) {
        cout << "Caught error: " << e.what() << endl;
    }

    return 0;
}
